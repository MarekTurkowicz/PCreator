using System.Globalization;

namespace LogLens.Generator;

/// <summary>Parses the generator command and writes CLEF to the supplied output.</summary>
public static class GeneratorCommand
{
    public static int Run(string[] args, TextWriter output, TextWriter error)
    {
        var count = 1;
        int? seed = null;
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
                else
                {
                    return Usage(error);
                }
            }
        }

        MinimalGenerator.Write(output, count, seed);
        return 0;
    }

    private static int Usage(TextWriter error)
    {
        error.WriteLine("Usage: generate [--count INTEGER] [--seed INTEGER] " +
                        "(count: 0..2147483647, default: 1; seed: signed 32-bit integer)");
        return 1;
    }
}
