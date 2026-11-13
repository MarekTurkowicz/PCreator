using Serilog;
using Serilog.Core;
using Serilog.Events;
using Serilog.Formatting.Compact;
using Serilog.Parsing;

namespace LogLens.Generator;

/// <summary>Emits Information events as newline-delimited CLEF.</summary>
public static class MinimalGenerator
{
    /// <summary>Writes events without taking ownership of the output writer.</summary>
    public static void Write(TextWriter output, int count = 1, int? seed = null)
    {
        ArgumentNullException.ThrowIfNull(output);
        ArgumentOutOfRangeException.ThrowIfNegative(count);
        using var logger = new LoggerConfiguration()
            .WriteTo.Sink(new ClefSink(output))
            .CreateLogger();

        // Seeded runs use a reproducible UTC start and never read the wall clock.
        var start = seed.HasValue
            ? DateTimeOffset.UnixEpoch.AddSeconds(new Random(seed.Value).Next(86400))
            : (DateTimeOffset?)null;
        var template = new MessageTemplateParser().Parse("Hello from LogLens");
        for (var index = 0; index < count; index++)
        {
            if (start.HasValue)
            {
                logger.Write(new LogEvent(start.Value.AddMilliseconds(index),
                    LogEventLevel.Information, null, template, Array.Empty<LogEventProperty>()));
            }
            else
            {
                logger.Information("Hello from LogLens");
            }
        }
        output.Flush();
    }

    private sealed class ClefSink(TextWriter output) : ILogEventSink
    {
        private readonly CompactJsonFormatter formatter = new();

        public void Emit(LogEvent logEvent) => formatter.Format(logEvent, output);
    }
}
