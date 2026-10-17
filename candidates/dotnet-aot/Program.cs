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
