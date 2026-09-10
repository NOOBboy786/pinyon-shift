"""Exercise the real WPF launcher without launching a game or touching user saves.

Run on Windows with .NET 8+: python tools/check-launcher.py [screenshot-directory]
"""
import pathlib
import subprocess
import sys
import tempfile
from xml.sax.saxutils import escape


ROOT = pathlib.Path(__file__).resolve().parents[1]
CHECK = r'''
using System;
using System.IO;
using System.IO.Compression;
using System.Reflection;
using System.Threading;
using System.Threading.Tasks;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Media;
using System.Windows.Media.Imaging;
using PinyonShift.Launcher;

class Check {
    static void Require(bool value, string message) {
        if (!value) throw new Exception(message);
    }
    [STAThread] static void Main(string[] args) {
        var app = new App();
        app.InitializeComponent();
        var window = new MainWindow(); // Never show: Loaded would start a real installation.
        SynchronizationContext.SetSynchronizationContext(null);
        var flags = BindingFlags.Instance | BindingFlags.NonPublic;
        var resolver = typeof(MainWindow).GetMethod("ResolveRepositoryRootAsync", flags)!;
        string Resolve(string selected) => ((Task<string>)resolver.Invoke(window, [selected])!).GetAwaiter().GetResult();
        bool CanChoose() => (bool)typeof(MainWindow).GetField("_canChooseInstallRoot", flags)!.GetValue(window)!;
        var root = AppContext.BaseDirectory;
        using (var zip = ZipFile.Open(Path.Combine(root, "pinyon-shift-source.zip"), ZipArchiveMode.Create)) {
            foreach (var name in new[] { "config/supported-dumps.json", "tools/setup-preview.ps1" }) {
                using var writer = new StreamWriter(zip.CreateEntry(name).Open());
                writer.Write("test payload");
            }
        }
        Environment.SetEnvironmentVariable("PINYON_SHIFT_INSTALL_ROOT", null);
        var selected = Path.Combine(root, "chosen folder with spaces");
        var installed = Resolve(selected);
        Require(installed.StartsWith(selected + Path.DirectorySeparatorChar), "Chosen folder ignored");
        Require(CanChoose(), "Packaged chooser disabled");
        var sentinel = Path.Combine(installed, "user-save-sentinel");
        File.WriteAllText(sentinel, "preserve");
        Require(Resolve(selected) == installed && File.ReadAllText(sentinel) == "preserve", "Existing files changed");
        var alternate = Path.Combine(root, "second installation");
        Require(Resolve(alternate).StartsWith(alternate), "Switch failed");
        Require(File.ReadAllText(sentinel) == "preserve", "Switch touched old installation");
        Environment.SetEnvironmentVariable("PINYON_SHIFT_INSTALL_ROOT", selected);
        Require(Resolve(alternate) == installed && !CanChoose(), "Environment precedence changed");
        Environment.SetEnvironmentVariable("PINYON_SHIFT_INSTALL_ROOT", null);
        try { Resolve(sentinel); throw new Exception("File accepted as installation root"); }
        catch (IOException) { }
        Require(CanChoose() && Resolve(selected) == installed, "Cannot recover after invalid folder");

        var button = (Button)window.FindName("ChooseInstallRootButton");
        var update = typeof(MainWindow).GetMethod("UpdatePrimaryButton", flags)!;
        update.Invoke(window, null);
        Require(button.IsEnabled, "Folder button unavailable");
        typeof(MainWindow).GetField("_busy", flags)!.SetValue(window, true);
        update.Invoke(window, null);
        Require(!button.IsEnabled, "Folder can change during build/play");
        typeof(MainWindow).GetField("_busy", flags)!.SetValue(window, false);
        update.Invoke(window, null);
        var label = (TextBlock)window.FindName("BuildLocationText");
        label.Text = @"D:\Games\A deliberately long installation directory\PinyonShift\source\0.1.0\.local\preview";
        ((FrameworkElement)window.FindName("LogPanel")).Visibility = Visibility.Visible;
        var log = (TextBox)window.FindName("LogTextBox");
        log.Text = "CMake Error: example failure\nThe complete diagnostic remains readable here.";
        var content = (FrameworkElement)window.Content;
        ((Panel)content).Background = window.Background;
        foreach (var size in new[] { new Size(1080, 720), new Size(920, 640) }) {
            content.Measure(size);
            content.Arrange(new Rect(size));
            content.UpdateLayout();
            Require(log.TranslatePoint(new Point(), (UIElement)log.Parent).Y > 0, "Log overlaps heading");
            if (args.Length != 0) {
                Directory.CreateDirectory(args[0]);
                var bitmap = new RenderTargetBitmap((int)size.Width, (int)size.Height, 96, 96, PixelFormats.Pbgra32);
                bitmap.Render(content);
                var png = new PngBitmapEncoder();
                png.Frames.Add(BitmapFrame.Create(bitmap));
                using var file = File.Create(Path.Combine(args[0], $"launcher-{size.Width}.png"));
                png.Save(file);
            }
            Require(button.ActualWidth > 0 && button.ActualHeight >= 24,
                $"Folder control clipped: {button.ActualWidth} x {button.ActualHeight}");
        }
        // Checkout detection takes precedence over packaged configuration.
        Directory.CreateDirectory(Path.Combine(root, "config"));
        Directory.CreateDirectory(Path.Combine(root, "tools"));
        File.WriteAllText(Path.Combine(root, "config/supported-dumps.json"), "{}");
        File.WriteAllText(Path.Combine(root, "tools/setup-preview.ps1"), "");
        Require(Path.TrimEndingDirectorySeparator(Resolve(selected)) == Path.TrimEndingDirectorySeparator(root)
            && !CanChoose(), "Checkout relocated");
        Console.WriteLine("Launcher folder selection, overrides, preservation, recovery and layout passed.");
        window.Close();
    }
}
'''


if __name__ == "__main__":
    with tempfile.TemporaryDirectory(prefix="pinyon-launcher-check-") as directory:
        project = pathlib.Path(directory)
        reference = escape(str(ROOT / "launcher/PinyonShift.Launcher/PinyonShift.Launcher.csproj"))
        (project / "Check.csproj").write_text(f'''<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup><OutputType>Exe</OutputType><TargetFramework>net8.0-windows</TargetFramework>
    <UseWPF>true</UseWPF><RuntimeIdentifier>win-x64</RuntimeIdentifier>
    <SelfContained>true</SelfContained></PropertyGroup>
  <ItemGroup><ProjectReference Include="{reference}" /></ItemGroup>
</Project>''')
        (project / "Program.cs").write_text(CHECK)
        subprocess.run(["dotnet", "run", "--project", str(project), "-c", "Release",
                        "--", *[str(pathlib.Path(p).resolve()) for p in sys.argv[1:]]], check=True)
