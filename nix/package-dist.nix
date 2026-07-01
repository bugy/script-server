{ lib, buildNpmPackage }:
let
  version = "1.18.0";
in
buildNpmPackage {
  pname = "script-server-dist";
  inherit version;

  src = ../web-src;

  npmDepsHash = "sha256-aBZDh2NcDU4OpsdTS8JqwGMa8WeIoyW9I6bUwTXfllU=";

  makeCacheWritable = true;

  # See <https://stackoverflow.com/questions/75959563/node-js-err-ossl-evp-unsupported-error-when-running-npm-run-start>
  NODE_OPTIONS = "--openssl-legacy-provider";

  installPhase = ''
    mkdir "$out"
    echo '${version}' > "$out/version.txt"
    cp -r ../web "$out"
  '';
}
