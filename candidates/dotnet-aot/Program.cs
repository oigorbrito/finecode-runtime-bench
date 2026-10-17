using System;
using System.IO;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;

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


// Deliberately bounded adapters: single-file literal grep and nonrecursive basename-glob find.
// No claim of full upstream grep/find tool parity.
if (args.Length == 3 && args[0] == "grep-subset")
{
    try
    {
        string file = args[1], needle = args[2];
        if (needle.Length == 0) { Environment.ExitCode = 2; return; }
        string[] lines = File.ReadAllText(file, Encoding.UTF8).Split('\n');
        var output = new System.Collections.Generic.List<string>();
        for (int i = 0; i < lines.Length; i++)
        {
            string line = lines[i].TrimEnd('\r');
            if (line.Contains(needle, StringComparison.Ordinal))
                output.Add($"{Path.GetFileName(file)}:{i + 1}: {line}");
        }
        Console.Write(output.Count == 0 ? "No matches found" : string.Join("\n", output));
        return;
    }
    catch (Exception e) when (e is IOException or UnauthorizedAccessException)
    {
        Console.Error.WriteLine("grep-subset failed: " + e.GetType().Name);
        Environment.ExitCode = 2;
        return;
    }
}
if (args.Length == 3 && args[0] == "find-subset")
{
    try
    {
        string root = args[1], pattern = args[2];
        if (!Directory.Exists(root)) { Console.Error.WriteLine("Path not found"); Environment.ExitCode = 2; return; }
        var output = new System.Collections.Generic.List<string>();
        foreach (string file in Directory.EnumerateFiles(root, "*", SearchOption.TopDirectoryOnly))
        {
            string name = Path.GetFileName(file);
            if (System.IO.Enumeration.FileSystemName.MatchesSimpleExpression(pattern, name, ignoreCase: false))
                output.Add(name);
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
