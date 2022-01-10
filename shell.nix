with import <nixpkgs> {};

mkShell {
  nativeBuildInputs = with buildPackages; [ 
    python38
    python38Packages.poetry
  ];
}
