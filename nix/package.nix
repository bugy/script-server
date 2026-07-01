let
  toml = builtins.fromTOML (builtins.readFile ./../pyproject.toml);
in
{
  lib,
  buildPythonPackage,
  tornado,
  setuptools,
}:
buildPythonPackage {
  pname = toml.project.name;
  version = toml.project.version;
  pyproject = true;

  src = lib.fileset.toSource {
    root = ./..;
    fileset = lib.fileset.unions [
      ./../pyproject.toml
      ./../src
    ];
  };

  build-system = [
    setuptools
  ];

  dependencies = [
    tornado
  ];
}
