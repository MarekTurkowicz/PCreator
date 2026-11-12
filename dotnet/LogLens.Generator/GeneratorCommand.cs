using System.Globalization;

namespace LogLens.Generator;

/// <summary>Parses the generator command and writes CLEF to the supplied output.</summary>
public static class GeneratorCommand
{
    public static int Run(string[] args, TextWriter output, TextWriter error)
    {
        var count = 1;
        if (args.Length != 0)
        {
            if (args[0] != "generate" || (args.Length != 1 && args.Length != 3))
            {
                return Usage(error);
            }

            if (args.Length == 3 &&
                (args[1] != "--count" ||
                 !int.TryParse(args[2], NumberStyles.None, CultureInfo.InvariantCulture, out count)))
            {
                return Usage(error);
            }
        }

        MinimalGenerator.Write(output, count);
        return 0;
    }

    private static int Usage(TextWriter error)
    {
        error.WriteLine("Usage: generate [--count INTEGER] (0..2147483647; default: 1)");
        return 1;
    }
}
