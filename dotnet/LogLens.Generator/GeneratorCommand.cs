using System.Globalization;

namespace LogLens.Generator;

/// <summary>Parses the generator command and writes CLEF to the supplied output.</summary>
public static class GeneratorCommand
{
    public static int Run(string[] args, TextWriter output, TextWriter error)
    {
        var count = 1;
        int? seed = null;
        var errorRate = 0.0;
        string? outputPath = null;
        if (args.Length != 0)
        {
            if (args[0] != "generate" || args.Length % 2 == 0)
            {
                return Usage(error);
            }

            var seen = new HashSet<string>();
            for (var index = 1; index < args.Length; index += 2)
            {
                var option = args[index];
                if (!seen.Add(option))
                {
                    return Usage(error);
                }

                if (option == "--count" &&
                    int.TryParse(args[index + 1], NumberStyles.None, CultureInfo.InvariantCulture, out var value))
                {
                    count = value;
                }
                else if (option == "--seed" &&
                         int.TryParse(args[index + 1], NumberStyles.AllowLeadingSign,
                             CultureInfo.InvariantCulture, out value))
                {
                    seed = value;
                }
                else if (option == "--error-rate" &&
                         double.TryParse(args[index + 1], NumberStyles.Float,
                             CultureInfo.InvariantCulture, out var rate) &&
                         double.IsFinite(rate) && rate >= 0 && rate <= 1)
                {
                    errorRate = rate;
                }
                else if (option == "--out" && !string.IsNullOrWhiteSpace(args[index + 1]))
                {
                    outputPath = args[index + 1];
                }
                else
                {
                    return Usage(error);
                }
            }
        }

        if (outputPath is null)
        {
            MinimalGenerator.Write(output, count, seed, errorRate);
            return 0;
        }

        try
        {
            // Overwrite the destination only after all arguments have been validated.
            using var file = new StreamWriter(outputPath, append: false,
                new System.Text.UTF8Encoding(encoderShouldEmitUTF8Identifier: false));
            MinimalGenerator.Write(file, count, seed, errorRate);
        }
        catch (Exception exception) when (exception is IOException or UnauthorizedAccessException
                                         or ArgumentException or NotSupportedException)
        {
            error.WriteLine($"Cannot write CLEF file: {exception.Message}");
            return 1;
        }
        return 0;
    }

    private static int Usage(TextWriter error)
    {
        error.WriteLine("Usage: generate [--count INTEGER] [--seed INTEGER] [--error-rate NUMBER] [--out PATH] " +
                        "(count: 0..2147483647, default: 1; seed: signed 32-bit integer; " +
                        "error-rate: 0..1, default: 0)");
        return 1;
    }
}
