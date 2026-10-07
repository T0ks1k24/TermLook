#!/bin/sh
# Start TermLook from the classic snap with its bundled Python, GTK, and VTE.
# Classic confinement shares the host environment, so shells must not inherit
# these overrides: record the original values for termlook.services.terminal.
set -eu

remember() {
    for name in "$@"; do
        if eval "[ -n \"\${$name+x}\" ]"; then
            eval "export TERMLOOK_SNAP_ORIG_$name=\"\$$name\""
        fi
    done
    export TERMLOOK_SNAP_RESTORE="$*"
}

case "$SNAP_ARCH" in
    amd64) triplet=x86_64-linux-gnu ;;
    arm64) triplet=aarch64-linux-gnu ;;
    *) echo "termlook: unsupported snap architecture: $SNAP_ARCH" >&2; exit 1 ;;
esac
lib="$SNAP/usr/lib/$triplet"

# Module caches contain revision-specific paths, so build them once per revision.
cache() {
    file=$1
    shift
    if [ ! -s "$file" ]; then
        mkdir -p "$SNAP_USER_DATA"
        "$@" > "$file.tmp"
        mv "$file.tmp" "$file"
    fi
}

remember LD_LIBRARY_PATH GI_TYPELIB_PATH XDG_DATA_DIRS GIO_MODULE_DIR GDK_PIXBUF_MODULE_FILE GTK_IM_MODULE_FILE

# GObject introspection opens libraries by soname, so the bundled ones must come first.
export LD_LIBRARY_PATH="$lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
export GI_TYPELIB_PATH="$lib/girepository-1.0"
# Bundled schemas first; host themes, icons, and fonts remain visible.
export XDG_DATA_DIRS="$SNAP/usr/share:${XDG_DATA_DIRS:-/usr/local/share:/usr/share}"
# The dconf backend reads the user's GNOME settings, such as fonts and dark style.
export GIO_MODULE_DIR="$lib/gio/modules"

export GDK_PIXBUF_MODULE_FILE="$SNAP_USER_DATA/gdk-pixbuf-loaders.cache"
cache "$GDK_PIXBUF_MODULE_FILE" "$lib/gdk-pixbuf-2.0/gdk-pixbuf-query-loaders" \
    "$lib"/gdk-pixbuf-2.0/2.10.0/loaders/*.so
export GTK_IM_MODULE_FILE="$SNAP_USER_DATA/gtk-immodules.cache"
cache "$GTK_IM_MODULE_FILE" "$lib/libgtk-3-0t64/gtk-query-immodules-3.0" \
    "$lib"/gtk-3.0/3.0.0/immodules/*.so

# -I keeps host PYTHONPATH and user site-packages out of the bundled interpreter.
exec "$SNAP/usr/bin/python3.12" -I "$SNAP/scripts/run.py" "$@"
