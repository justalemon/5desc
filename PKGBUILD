pkgname=5desc
pkgver=r74.a34b96f
pkgrel=1
pkgdesc="Tool to create 5mods descriptions from Markdown files"
arch=("x86_64")
url="https://github.com/justalemon/$pkgname"
license=("MIT")
depends=()
makedepends=("python"
             "python-marko>=2.0.0"
             "python-dulwich>=0.21.6"
             "python-requests>=2.31.0"
             "patchelf"
             "ccache")
provides=("${pkgname%-git}")
source=("src-$pkgname::git+${url}.git")
sha256sums=('SKIP')

pkgver() {
    cd "src-$pkgname"
    printf "r%s.%s" "$(git rev-list --count HEAD)" "$(git rev-parse --short=7 HEAD)"
}

build() {
    cd "src-$pkgname"
    python -m nuitka --standalone --onefile --output-filename="5desc" --assume-yes-for-downloads fivedesc.py
}

package() {
    cd "src-$pkgname"
    install -m 775 -DT "$srcdir/src-$pkgname/5desc" "$pkgdir/usr/bin/$pkgname"
}
