using System;
using System.Diagnostics;
using System.Threading;
using System.Threading.Tasks;

internal static class BoundedChild
{
    internal static async Task<(bool TimedOut, int ExitCode, string Stdout, string Stderr)>
        Run(ProcessStartInfo info, int deadlineMs)
    {
        using var process = Process.Start(info) ?? throw new System.IO.IOException("Child start failed");
        Task<string> stdout = process.StandardOutput.ReadToEndAsync();
        Task<string> stderr = process.StandardError.ReadToEndAsync();
        using var timeout = new CancellationTokenSource(deadlineMs);
        try
        {
            await process.WaitForExitAsync(timeout.Token);
        }
        catch (OperationCanceledException)
        {
            if (!process.HasExited) process.Kill(entireProcessTree: true);
            await process.WaitForExitAsync();
            // Finish draining both streams even after killing the process tree.
            await Task.WhenAll(stdout, stderr).WaitAsync(TimeSpan.FromSeconds(5));
            return (true, 124, await stdout, await stderr);
        }
        return (false, process.ExitCode, await stdout, await stderr);
    }
}
