using System;
using System.IO;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using System.Text.RegularExpressions;
using System.Diagnostics;

if (args.Length == 1 && args[0] == "--help")
{
    Console.WriteLine("finecode-dotnet-aot-probe --help | --version | scan-file <path> <literal>");
    return;
}
if (args.Length == 1 && args[0] == "--version")
{
    Console.WriteLine("0.2.0-probe");
    return;
}
// Deliberate in-container memory exhaustion under Docker's 128 MiB cgroup.
// The test uses a separate disposable container and must never run on host.
if (args.Length == 1 && args[0] == "sandbox-memory-probe")
{
    byte[] allocated = new byte[512 * 1024 * 1024];
    for (int i = 0; i < allocated.Length; i += 4096)
        allocated[i] = 1;
    GC.KeepAlive(allocated);
    Console.WriteLine("MEMORY_ALLOCATION_COMPLETED");
    return;
}

// Docker-only negative boundary probe. Never claims host-wide sandbox isolation.
// The CI launches this as non-root, read-only, no-network and no-capability.
if (args.Length == 1 && args[0] == "sandbox-probe")
{
    bool readonlyDenied = false;
    bool tmpfsWritable = false;
    bool networkDenied = false;
    bool noEffectiveCaps = false;
    string nonce = Guid.NewGuid().ToString("N");
    try
    {
        File.WriteAllText("/var/tmp/finecode-" + nonce, "forbidden");
    }
    catch (Exception e) when (e is IOException or UnauthorizedAccessException)
    {
        readonlyDenied = true;
    }
    try
    {
        string tempFile = Path.Combine("/tmp", "finecode-" + nonce);
        File.WriteAllText(tempFile, "temporary");
        tmpfsWritable = File.ReadAllText(tempFile) == "temporary";
        File.Delete(tempFile);
    }
    catch (Exception e) when (e is IOException or UnauthorizedAccessException) { }
    try
    {
        using var client = new System.Net.Sockets.TcpClient();
        using var deadline = new CancellationTokenSource(TimeSpan.FromMilliseconds(1000));
        await client.ConnectAsync(System.Net.IPAddress.Parse("1.1.1.1"), 53, deadline.Token);
    }
    catch (Exception e) when (e is System.Net.Sockets.SocketException or OperationCanceledException)
    {
        networkDenied = true;
    }
    try
    {
        string status = File.ReadAllText("/proc/self/status");
        noEffectiveCaps = status.Split('\n').Any(line => line.StartsWith("CapEff:", StringComparison.Ordinal)
            && line["CapEff:".Length..].Trim().TrimStart('0').Length == 0);
    }
    catch (Exception e) when (e is IOException or UnauthorizedAccessException) { }
    using (var writer = new Utf8JsonWriter(Console.OpenStandardOutput()))
    {
        writer.WriteStartObject();
        writer.WriteString("kind", "docker_sandbox_negative_boundary_probe");
        writer.WriteBoolean("readonly_root_denied", readonlyDenied);
        writer.WriteBoolean("tmpfs_writable", tmpfsWritable);
        writer.WriteBoolean("external_tcp_denied", networkDenied);
        writer.WriteBoolean("effective_capabilities_zero", noEffectiveCaps);
        writer.WriteEndObject();
        writer.Flush();
    }
    Console.WriteLine();
    if (!readonlyDenied || !tmpfsWritable || !networkDenied || !noEffectiveCaps)
        Environment.ExitCode = 1;
    return;
}

// Deterministic process-tree safety fixture; NOT Pi tool parity or production command.
if (args.Length == 3 && args[0] == "process-tree-probe")
{
    string markerDir = args[1];
    if (!int.TryParse(args[2], out int deadline) || deadline < 1 || deadline > 60000)
    {
        Console.Error.WriteLine("Invalid process-tree deadline");
        Environment.ExitCode = 2;
        return;
    }
    Directory.CreateDirectory(markerDir);
    string self = Environment.ProcessPath ?? throw new IOException("Missing executable path");
    var start = new ProcessStartInfo(self)
    {
        UseShellExecute = false,
        RedirectStandardOutput = true,
        RedirectStandardError = true
    };
    start.ArgumentList.Add("process-tree-parent");
    start.ArgumentList.Add(markerDir);
    var result = await BoundedChild.Run(start, deadline);
    if (result.TimedOut)
    {
        Console.Write("PROCESS_TREE_TIMEOUT");
        Environment.ExitCode = 124;
    }
    else
    {
        Console.Error.WriteLine("Process unexpectedly completed");
        Environment.ExitCode = 1;
    }
    return;
}
if (args.Length == 2 && args[0] == "process-tree-parent")
{
    File.WriteAllText(Path.Combine(args[1], "parent-started.txt"), "PARENT_STARTED");
    string self = Environment.ProcessPath ?? throw new IOException("Missing executable path");
    var grandchild = new ProcessStartInfo(self) { UseShellExecute = false };
    grandchild.ArgumentList.Add("process-tree-grandchild");
    grandchild.ArgumentList.Add(args[1]);
    using var p = Process.Start(grandchild) ?? throw new IOException("Unable to spawn grandchild");
    await Task.Delay(3500);
    File.WriteAllText(Path.Combine(args[1], "parent-survived.txt"), "PARENT_SURVIVED");
    await p.WaitForExitAsync();
    return;
}
if (args.Length == 2 && args[0] == "process-tree-grandchild")
{
    File.WriteAllText(Path.Combine(args[1], "grandchild-started.txt"), "GRANDCHILD_STARTED");
    await Task.Delay(3500);
    File.WriteAllText(Path.Combine(args[1], "grandchild-survived.txt"), "GRANDCHILD_SURVIVED");
    return;
}

// Bounded Pi read-text subset: text-only, below upstream truncation thresholds.
if (args.Length >= 2 && args.Length <= 4 && args[0] == "read-subset")
{
    if (args.Length >= 3 && !int.TryParse(args[2], out _))
    {
        Console.Error.WriteLine("Invalid offset");
        Environment.ExitCode = 2;
        return;
    }
    if (args.Length == 4 && (!int.TryParse(args[3], out int parsedLimit) || parsedLimit < 0))
    {
        Console.Error.WriteLine("Invalid limit");
        Environment.ExitCode = 2;
        return;
    }
    int offset = args.Length >= 3 ? int.Parse(args[2]) : 1;
    int? limit = args.Length == 4 ? int.Parse(args[3]) : null;
    try
    {
        string text = File.ReadAllText(args[1], Encoding.UTF8);
        string[] allLines = text.Split('\n');
        int startLine = offset == 0 ? 0 : Math.Max(0, offset - 1);
        if (startLine >= allLines.Length)
        {
            Console.Error.WriteLine($"Offset {offset} is beyond end of file ({allLines.Length} lines total)");
            Environment.ExitCode = 2;
            return;
        }
        int endLine = limit.HasValue ? (int)Math.Min((long)startLine + limit.Value, allLines.Length) : allLines.Length;
        string selected = string.Join("\n", allLines[startLine..endLine]);
        if (Encoding.UTF8.GetByteCount(selected) > 32 * 1024 || endLine - startLine > 2000)
        {
            Console.Error.WriteLine("Outside bounded read-subset: upstream truncation semantics are not implemented");
            Environment.ExitCode = 3;
            return;
        }
        if (limit.HasValue && endLine < allLines.Length)
        {
            int remaining = allLines.Length - endLine;
            selected += $"\n\n[{remaining} more lines in file. Use offset={endLine + 1} to continue.]";
        }
        Console.Write(selected);
        return;
    }
    catch (Exception e) when (e is IOException or UnauthorizedAccessException)
    {
        Console.Error.WriteLine("read-subset failed: " + e.GetType().Name);
        Environment.ExitCode = 2;
        return;
    }
}


// Bounded single-file grep: literal/regex and optional case folding, no context/globs/ignore.
if (args.Length >= 3 && args.Length <= 5 && args[0] == "grep-subset")
{
    string file = args[1], pattern = args[2];
    string mode = args.Length >= 4 ? args[3] : "literal";
    bool ignoreCase = args.Length >= 5 && args[4] == "ignore-case";
    if (pattern.Length == 0 || (mode != "literal" && mode != "regex") ||
        (args.Length == 5 && args[4] != "ignore-case"))
    {
        Console.Error.WriteLine("Invalid grep-subset arguments");
        Environment.ExitCode = 2;
        return;
    }
    try
    {
        Regex? regex = mode == "regex" ?
            new Regex(pattern, RegexOptions.CultureInvariant |
                (ignoreCase ? RegexOptions.IgnoreCase : RegexOptions.None),
                TimeSpan.FromSeconds(1)) : null;
        string[] lines = File.ReadAllText(file, Encoding.UTF8).Split('\n');
        var output = new System.Collections.Generic.List<string>();
        for (int i = 0; i < lines.Length; i++)
        {
            string line = lines[i].TrimEnd('\r');
            bool matched = regex is not null ? regex.IsMatch(line) :
                line.Contains(pattern, ignoreCase ? StringComparison.OrdinalIgnoreCase : StringComparison.Ordinal);
            if (matched) output.Add($"{Path.GetFileName(file)}:{i + 1}: {line}");
        }
        Console.Write(output.Count == 0 ? "No matches found" : string.Join("\n", output));
        return;
    }
    catch (Exception e) when (e is IOException or UnauthorizedAccessException
        or ArgumentException or RegexMatchTimeoutException)
    {
        Console.Error.WriteLine("grep-subset failed: " + e.GetType().Name);
        Environment.ExitCode = 2;
        return;
    }
}
// Bounded recursive file discovery using basename glob. No .gitignore or directory matches.
if (args.Length == 3 && args[0] == "find-subset")
{
    try
    {
        string root = args[1], pattern = args[2];
        if (!Directory.Exists(root)) { Console.Error.WriteLine("Path not found"); Environment.ExitCode = 2; return; }
        var output = new System.Collections.Generic.List<string>();
        foreach (string file in Directory.EnumerateFiles(root, "*", SearchOption.AllDirectories))
        {
            string name = Path.GetFileName(file);
            if (System.IO.Enumeration.FileSystemName.MatchesSimpleExpression(pattern, name, ignoreCase: false))
                output.Add(Path.GetRelativePath(root, file).Replace('\\', '/'));
        }
        output.Sort(StringComparer.Ordinal);
        Console.Write(output.Count == 0 ? "No files found matching pattern" : string.Join("\n", output));
        return;
    }
    catch (Exception e) when (e is IOException or UnauthorizedAccessException)
    {
        Console.Error.WriteLine("find-subset failed: " + e.GetType().Name);
        Environment.ExitCode = 2;
        return;
    }
}


// Delegate-only compatibility experiment: share Pi's fd engine. Native AOT does
// not subsume fd: the caller must explicitly supply its resolved executable.
if (args.Length >= 4 && args.Length <= 6 && args[0] == "find-fd-subset")
{
    string root = Path.GetFullPath(args[1]);
    string pattern = args[2];
    string fdPath = args[3];
    int maxResults = args.Length >= 5 && int.TryParse(args[4], out int n) ? n : 1000;
    int timeoutMs = args.Length == 6 && int.TryParse(args[5], out int t) ? t : 15000;
    if (!Directory.Exists(root) || pattern.Length == 0 || fdPath.Length == 0 ||
        maxResults < 1 || maxResults > 1000 || timeoutMs < 1 || timeoutMs > 60000 ||
        (args.Length >= 5 && !int.TryParse(args[4], out _)) ||
        (args.Length == 6 && !int.TryParse(args[5], out _)))
    {
        Console.Error.WriteLine("find-fd-subset: invalid directory, pattern or fd");
        Environment.ExitCode = 2;
        return;
    }
    try
    {
        var start = new ProcessStartInfo(fdPath)
        {
            UseShellExecute = false,
            RedirectStandardOutput = true,
            RedirectStandardError = true
        };
        start.ArgumentList.Add("--glob");
        start.ArgumentList.Add("--color=never");
        start.ArgumentList.Add("--hidden");
        bool inGitRepo = false;
        for (string? current = root; current is not null; current = Directory.GetParent(current)?.FullName)
        {
            if (Directory.Exists(Path.Combine(current, ".git")) ||
                File.Exists(Path.Combine(current, ".git")))
            {
                inGitRepo = true;
                break;
            }
        }
        if (!inGitRepo) start.ArgumentList.Add("--no-require-git");
        start.ArgumentList.Add("--max-results");
        start.ArgumentList.Add(maxResults.ToString(System.Globalization.CultureInfo.InvariantCulture));
        if (pattern.Contains('/'))
        {
            start.ArgumentList.Add("--full-path");
            if (!pattern.StartsWith('/') && !pattern.StartsWith("**/") && pattern != "**")
                pattern = "**/" + pattern;
            if (OperatingSystem.IsWindows()) pattern = pattern.Replace("/", @"[/\\]");
        }
        start.ArgumentList.Add("--");
        start.ArgumentList.Add(pattern);
        start.ArgumentList.Add(root);
        var execution = await BoundedChild.Run(start, timeoutMs);
        if (execution.TimedOut)
        {
            Console.Error.WriteLine("find-fd-subset timeout");
            Environment.ExitCode = 124;
            return;
        }
        string stdout = execution.Stdout;
        string stderr = execution.Stderr;
        if (execution.ExitCode != 0 && stdout.Length == 0)
        {
            Console.Error.WriteLine("fd failed: " + stderr.Trim());
            Environment.ExitCode = 2;
            return;
        }
        var results = new System.Collections.Generic.List<string>();
        foreach (string raw in stdout.Split('\n', StringSplitOptions.RemoveEmptyEntries))
        {
            string candidate = raw.TrimEnd('\r').Trim();
            if (candidate.Length == 0) continue;
            bool directorySuffix = candidate.EndsWith('/') || candidate.EndsWith('\\');
            string relative = Path.IsPathRooted(candidate) ? Path.GetRelativePath(root, candidate) : candidate;
            relative = relative.Replace('\\', '/');
            if (directorySuffix && !relative.EndsWith('/')) relative += "/";
            results.Add(relative);
        }
        if (results.Count == 0)
        {
            Console.Write("No files found matching pattern");
        }
        else
        {
            Console.Write(string.Join("\n", results));
            if (results.Count >= maxResults)
                Console.Write($"\n\n[{maxResults} results limit reached. Use limit={maxResults * 2} for more, or refine pattern]");
        }
        return;
    }
    catch (Exception e) when (e is IOException or UnauthorizedAccessException
        or System.ComponentModel.Win32Exception)
    {
        Console.Error.WriteLine("find-fd-subset failed: " + e.GetType().Name);
        Environment.ExitCode = 2;
        return;
    }
}

if (args.Length == 3 && args[0] == "scan-file")
{
    if (args[2].Length == 0)
    {
        Console.Error.WriteLine("Search literal must not be empty.");
        Environment.ExitCode = 2;
        return;
    }
    try
    {
        byte[] bytes = File.ReadAllBytes(args[1]);
        string contents = new UTF8Encoding(false, true).GetString(bytes);
        int matches = 0;
        int offset = 0;
        while (true)
        {
            int found = contents.IndexOf(args[2], offset, StringComparison.Ordinal);
            if (found < 0) break;
            matches++;
            offset = found + args[2].Length; // Nonoverlapping, ordinal matches.
        }
        int lines = contents.Length == 0 ? 0 : 1;
        for (int i = 0; i < contents.Length; i++)
        {
            if (contents[i] == '\n') lines++;
        }
        if (contents.EndsWith("\n", StringComparison.Ordinal)) lines--;

        using var writer = new Utf8JsonWriter(Console.OpenStandardOutput());
        writer.WriteStartObject();
        writer.WriteString("schema", "finecode-process-probe-scan-v1");
        writer.WriteNumber("bytes", bytes.Length);
        writer.WriteNumber("lines", lines);
        writer.WriteNumber("matches", matches);
        writer.WriteString("sha256", Convert.ToHexString(SHA256.HashData(bytes)).ToLowerInvariant());
        writer.WriteEndObject();
        writer.Flush();
        Console.WriteLine();
        return;
    }
    catch (Exception e) when (e is IOException or UnauthorizedAccessException or DecoderFallbackException)
    {
        Console.Error.WriteLine("scan-file failed: " + e.GetType().Name);
        Environment.ExitCode = 2;
        return;
    }
}
Console.Error.WriteLine("Unsupported arguments; this is a bounded process probe, NOT a Pi agent.");
Environment.ExitCode = 2;
