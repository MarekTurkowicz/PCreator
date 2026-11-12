using Serilog;
using Serilog.Core;
using Serilog.Events;
using Serilog.Formatting.Compact;

namespace LogLens.Generator;

/// <summary>Emits one Information event as newline-delimited CLEF.</summary>
public static class MinimalGenerator
{
    /// <summary>Writes an event without taking ownership of the output writer.</summary>
    public static void Write(TextWriter output)
    {
        ArgumentNullException.ThrowIfNull(output);
        using var logger = new LoggerConfiguration()
            .WriteTo.Sink(new ClefSink(output))
            .CreateLogger();

        logger.Information("Hello from LogLens");
        output.Flush();
    }

    private sealed class ClefSink(TextWriter output) : ILogEventSink
    {
        private readonly CompactJsonFormatter formatter = new();

        public void Emit(LogEvent logEvent) => formatter.Format(logEvent, output);
    }
}
