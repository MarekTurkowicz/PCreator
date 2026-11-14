using Serilog;
using Serilog.Core;
using Serilog.Events;
using Serilog.Formatting.Compact;
using Serilog.Parsing;

namespace LogLens.Generator;

/// <summary>Emits Information events as newline-delimited CLEF.</summary>
public static class MinimalGenerator
{
    /// <summary>
    /// Writes successful GET requests to three endpoints with Elapsed in milliseconds
    /// from 0.1 to 500.0, without taking ownership of the output writer.
    /// </summary>
    public static void Write(TextWriter output, int count = 1, int? seed = null)
    {
        ArgumentNullException.ThrowIfNull(output);
        ArgumentOutOfRangeException.ThrowIfNegative(count);
        using var logger = new LoggerConfiguration()
            .WriteTo.Sink(new ClefSink(output))
            .CreateLogger();

        // Seeded runs use a reproducible UTC start and never read the wall clock.
        var random = seed.HasValue ? new Random(seed.Value) : new Random();
        var start = seed.HasValue
            ? DateTimeOffset.UnixEpoch.AddSeconds(random.Next(86400))
            : (DateTimeOffset?)null;
        string[] endpoints = ["/api/orders", "/api/products", "/health"];
        var template = new MessageTemplateParser().Parse("Hello from LogLens");
        for (var index = 0; index < count; index++)
        {
            LogEventProperty[] properties =
            [
                new("RequestPath", new ScalarValue(endpoints[random.Next(endpoints.Length)])),
                new("RequestMethod", new ScalarValue("GET")),
                new("StatusCode", new ScalarValue(200)),
                new("Elapsed", new ScalarValue(random.Next(1, 5001) / 10.0)),
            ];
            logger.Write(new LogEvent(start?.AddMilliseconds(index) ?? DateTimeOffset.UtcNow,
                LogEventLevel.Information, null, template, properties));
        }
        output.Flush();
    }

    private sealed class ClefSink(TextWriter output) : ILogEventSink
    {
        private readonly CompactJsonFormatter formatter = new();

        public void Emit(LogEvent logEvent) => formatter.Format(logEvent, output);
    }
}
