# Maintainer: zcharka <https://github.com/zcharka>

pkgname=arc-store
pkgver=1.0.0
pkgrel=11
pkgdesc='Arc Store - a graphical package manager for pacman and the AUR'
url='https://github.com/zcharka'
arch=('any')
license=('GPL-3.0')
depends=(
  'python-gobject'
  'gtk4'
  'libadwaita'
  'python'
  'desktop-file-utils'
  'hicolor-icon-theme'
)
optdepends=(
  'flatpak: search, install, and remove Flatpak apps from both tabs'
  'paru: faster/automated AUR builds (falls back to makepkg otherwise)'
  'webkitgtk-6.0: show live Arch Wiki pages inside the package detail view'
)
install=arc-store.install

package() {
    cd "${srcdir}"

    find usr -type f | while IFS= read -r _file; do
        if [[ "${_file}" == usr/bin/* ]]; then
            install -Dm755 "${_file}" "${pkgdir}/${_file}"
        else
            install -Dm644 "${_file}" "${pkgdir}/${_file}"
        fi
    done
}
