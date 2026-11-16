using LogLens.Generator;
using Xunit;

namespace LogLens.Generator.Tests;

public class FileOutputTests
{
    [Fact]
    public void FileOutputMatchesSharedClefSampleAndCanBeOverwritten()
    {
        var directory = Directory.CreateTempSubdirectory("loglens-");
        try
        {
            var path = Path.Combine(directory.FullName, "generated logs.clef");
            using var output = new StringWriter();
            using var error = new StringWriter();
            Assert.Equal(0, GeneratorCommand.Run(
                ["generate", "--out", path, "--seed", "42", "--error-rate", "1"], output, error));
            var sample = Path.Combine(AppContext.BaseDirectory, "dotnet-error.clef");
            Assert.InRange(new FileInfo(sample).Length, 1L, 200_000L - 1);
            Assert.Equal(File.ReadAllText(sample).TrimEnd(), File.ReadAllText(path).TrimEnd());
            Assert.Equal("", output.ToString());
            Assert.Equal("", error.ToString());

            Assert.Equal(0, GeneratorCommand.Run(
                ["generate", "--out", path, "--count", "0"], output, error));
            Assert.Empty(File.ReadAllBytes(path));
        }
        finally
        {
            directory.Delete(true);
        }
    }

    [Fact]
    public void InvalidArgumentsLeaveExistingFileUntouched()
    {
        var path = Path.GetTempFileName();
        try
        {
            File.WriteAllText(path, "keep");
            using var output = new StringWriter();
            using var error = new StringWriter();
            Assert.Equal(1, GeneratorCommand.Run(
                ["generate", "--out", path, "--count", "invalid"], output, error));
            Assert.Equal("keep", File.ReadAllText(path));
        }
        finally
        {
            File.Delete(path);
        }
    }

    [Fact]
    public void UnwritableDestinationReportsErrorWithoutStdout()
    {
        using var output = new StringWriter();
        using var error = new StringWriter();
        Assert.Equal(1, GeneratorCommand.Run(
            ["generate", "--out", Path.GetTempPath()], output, error));
        Assert.Equal("", output.ToString());
        Assert.Contains("Cannot write CLEF file:", error.ToString());
    }

    [Theory]
    [InlineData("generate", "--out")]
    [InlineData("generate", "--out", "")]
    [InlineData("generate", "--out", " ")]
    [InlineData("generate", "--out", "a", "--out", "b")]
    public void InvalidOutputOptionShowsUsage(params string[] args)
    {
        using var output = new StringWriter();
        using var error = new StringWriter();
        Assert.Equal(1, GeneratorCommand.Run(args, output, error));
        Assert.Equal("", output.ToString());
        Assert.Contains("Usage:", error.ToString());
    }
}
