pkgname=5desc
pkgver=r1
pkgrel=1
pkgdesc="Tool to create 5mods descriptions from Markdown files"
arch=("any")
url="https://github.com/justalemon/$pkgname"
license=("MIT")
depends=("python"
         "python-marko>=2.0.0"
         "python-dulwich>=0.21.6"
         "python-requests>=2.31.0")
makedepends=()
provides=("${pkgname%-git}")
source=("src-$pkgname::git+${url}.git")
sha256sums=('SKIP')

pkgver() {
    cd "src-$pkgname"
    printf "r%s.%s" "$(git rev-list --count HEAD)" "$(git rev-parse --short=7 HEAD)"
}

package() {
    cd "src-$pkgname"
    install -m 644 -DT "$startdir/fivedesc.py" "$pkgdir/usr/bin/$pkgname"
}
