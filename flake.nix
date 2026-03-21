{
  description = "ByteIO - COD Order Confirmation";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-24.11";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs { inherit system; };
        
        pythonPackages = pkgs.python311.withPackages (ps: with ps; [
          fastapi
          pydantic
          uvicorn
          jinja2
          python-multipart
          httpx
          python-dateutil
        ]);
        
        app = pkgs.stdenv.mkDerivation {
          pname = "byteio-api";
          version = "1.0.0";
          src = ./.;
          installPhase = ''
            cp -r . $out
          '';
        };
        
        startScript = pkgs.writeShellScriptBin "start.sh" ''
          #!${pkgs.bash}/bin/bash
          set -e
          cd ${app}
          exec ${pythonPackages}/bin/uvicorn src.main:app --host 0.0.0.0 --port 8000
        '';
      in
      {
        devShells.default = pkgs.mkShell {
          buildInputs = [ pythonPackages ];
        };

        defaultPackage = pkgs.dockerTools.buildImage {
          name = "byteio-cod-confirmation";
          tag = "latest";
          copyToRoot = [
            startScript
            pkgs.bash
            pkgs.coreutils
          ];
          config = {
            Cmd = [ "${startScript}/bin/start.sh" ];
          };
        };
      }
    );
}
