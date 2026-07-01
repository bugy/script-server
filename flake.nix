{
  description = "Script-server";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/26.05";

    flake-parts.url = "github:hercules-ci/flake-parts";
  };

  outputs =
    inputs@{
      self,
      nixpkgs,
      flake-parts,
      ...
    }:
    flake-parts.lib.mkFlake { inherit inputs; } {
      flake = {
        overlays.default = final: prev: {
          script-server = final.python3Packages.callPackage ./nix/package.nix { };

          script-server-dist = final.callPackage ./nix/package-dist.nix { };
        };

        nixosModules.default = import ./nix/module.nix;
      };

      systems = [
        "x86_64-linux"
        "aarch64-linux"
        "aarch64-darwin"
      ];

      perSystem =
        { pkgs, ... }:
        {
          packages = {
            script-server = pkgs.python3Packages.callPackage ./nix/package.nix { };

            script-server-dist = pkgs.callPackage ./nix/package-dist.nix { };
          };

          formatter = pkgs.nixfmt-tree;
        };
    };
}
