manual-test-coverage

Run the packaged tool with the platform launcher:

Windows:
  .\run-coverage.ps1 -Target C:\path\app.exe -FunctionInfos C:\path\info

macOS/Linux:
  ./run-coverage.sh --target /path/app --function_infos /path/info

Optional arguments:
  --output_dir / -OutputDir
  --included_modules / -IncludedModules
  --pid / -Pid
  --agent-script / -AgentScript
