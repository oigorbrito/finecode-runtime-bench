using System;
using System.Runtime.InteropServices;

if (args.Length == 1 && args[0] == "--help")
{
    Console.WriteLine("finecode-dotnet-aot-probe --help");
    return;
}
if (args.Length == 1 && args[0] == "--version")
{
    Console.WriteLine("0.1.0-probe");
    return;
}
Console.Error.WriteLine("This is a native-AOT process probe, NOT a Pi agent implementation.");
Environment.ExitCode = 2;
