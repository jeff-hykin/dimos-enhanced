nixi bash
nixi direnv
nixi nix-direnv

echo '
eval "$(direnv hook zsh)"' >> ~/.zshrc

direnv allow
direnv reload