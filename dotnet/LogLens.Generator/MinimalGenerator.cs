using Serilog;
using Serilog.Core;
using Serilog.Events;
using Serilog.Formatting.Compact;

namespace LogLens.Generator;

/// <summary>Emits Information events as newline-delimited CLEF.</summary>
public static class MinimalGenerator
{
    /// <summary>Writes events without taking ownership of the output writer.</summary>
    public static void Write(TextWriter output, int count = 1)
    {
        ArgumentNullException.ThrowIfNull(output);
        ArgumentOutOfRangeException.ThrowIfNegative(count);
        using var logger = new LoggerConfiguration()
            .WriteTo.Sink(new ClefSink(output))
            .CreateLogger();

        for (var index = 0; index < count; index++)
        {
            logger.Information("Hello from LogLens");
        }
        output.Flush();
    }

    private sealed class ClefSink(TextWriter output) : ILogEventSink
    {
        private readonly CompactJsonFormatter formatter = new();

        public void Emit(LogEvent logEvent) => formatter.Format(logEvent, output);
    }
}
