using Serilog;
using Serilog.Core;
using Serilog.Events;
using Serilog.Formatting.Compact;
using Serilog.Parsing;

namespace LogLens.Generator;

/// <summary>Emits HTTP events as newline-delimited CLEF.</summary>
public static class MinimalGenerator
{
    /// <summary>
    /// Writes GET requests with Elapsed from 0.1 to 500.0 milliseconds.
    /// Error rate is a probability from 0 to 1 (default 0); failures have status 500
    /// and an exception. Does not take ownership of the output writer.
    /// </summary>
    public static void Write(TextWriter output, int count = 1, int? seed = null, double errorRate = 0)
    {
        ArgumentNullException.ThrowIfNull(output);
        ArgumentOutOfRangeException.ThrowIfNegative(count);
        if (!double.IsFinite(errorRate) || errorRate < 0 || errorRate > 1)
        {
            throw new ArgumentOutOfRangeException(nameof(errorRate), "Expected a probability from 0 to 1.");
        }
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
            var failed = errorRate == 1 || (errorRate > 0 && random.NextDouble() < errorRate);
            LogEventProperty[] properties =
            [
                new("RequestPath", new ScalarValue(endpoints[random.Next(endpoints.Length)])),
                new("RequestMethod", new ScalarValue("GET")),
                new("StatusCode", new ScalarValue(failed ? 500 : 200)),
                new("Elapsed", new ScalarValue(random.Next(1, 5001) / 10.0)),
            ];
            logger.Write(new LogEvent(start?.AddMilliseconds(index) ?? DateTimeOffset.UtcNow,
                failed ? LogEventLevel.Error : LogEventLevel.Information,
                failed ? new InvalidOperationException("Request failed") : null, template, properties));
        }
        output.Flush();
    }

    private sealed class ClefSink(TextWriter output) : ILogEventSink
    {
        private readonly CompactJsonFormatter formatter = new();

        public void Emit(LogEvent logEvent) => formatter.Format(logEvent, output);
    }
}
