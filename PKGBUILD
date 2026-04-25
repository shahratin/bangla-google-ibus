# Maintainer: Mahmud <your@email.com>
pkgname=bangla-google-ibus
pkgver=1.0.0
pkgrel=1
pkgdesc="Bangla phonetic input engine for IBus using Google Input Tools"
arch=('any')
url="https://github.com/yourusername/bangla-google-ibus"
license=('MIT')
depends=('ibus' 'python' 'python-gobject' 'ibus-autostart')
source=("git+https://github.com/shahratin/bangla-google-ibus.git")
sha256sums=('SKIP')

package() {
    cd "$srcdir/bangla-google-ibus"

    # Engine script
    install -Dm644 bangla_engine.py \
        "$pkgdir/usr/lib/bangla-google-ibus/bangla_engine.py"

    # IBus component XML
    install -Dm644 bangla-google.xml \
        "$pkgdir/usr/share/ibus/component/bangla-google.xml"

    # Systemd user service
    install -Dm644 bangla-engine.service \
        "$pkgdir/usr/lib/systemd/user/bangla-engine.service"
}

post_install() {
    systemctl --user daemon-reload
    systemctl --user enable --now bangla-engine.service
    ibus restart
    echo ">>> Switch to 'Bangla (Google)' in ibus-setup under Input Method tab"
}

post_remove() {
    systemctl --user disable --now bangla-engine.service
    systemctl --user daemon-reload
    ibus restart
}
