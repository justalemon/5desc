#!/usr/bin/env bash

TARGET_EUID=$EUID

if [[ $TARGET_EUID == "0" ]]; then
    TARGET_EUID="1"
fi

rm -r "build/marko" || true
git clone "https://aur.archlinux.org/python-marko.git" "build/marko"
(cd build/marko || exit 1; env EUID=$TARGET_EUID makepkg -sf --noconfirm)
mkdir dist || true
cp build/marko/*.tar.* dist/
