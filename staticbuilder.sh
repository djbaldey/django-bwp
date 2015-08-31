#!/usr/bin/env bash

if [ -f 'bwp/__init__.py' ]
then
    VERSION=$(python -c 'import bwp; print(bwp.get_version());');
else
    echo 'This script must be run from it directory!';
    exit 1;
fi;


echo "BWP version: ${VERSION}";
echo '';

SRC_DIR="bwp/static_src";
DST_DIR="bwp/static/bwp";

CSS_SYM="../../static_src/css";
JS_SYM="../../static_src/js";
IMG_SYM="../../static_src/img";

VERSION_DIR="${DST_DIR}/${VERSION}";
CSS_DIR="${VERSION_DIR}/css";
JS_DIR="${VERSION_DIR}/js";
IMG_DIR="${VERSION_DIR}/img";
#~ IMG_DIR="${DST_DIR}/img";

[ -d ${DST_DIR} ] && rm -R ${DST_DIR};
mkdir -p ${CSS_DIR} ${JS_DIR} ${IMG_DIR};

# symlinks for develop dirs
echo 'SYMLINKS FOR DEVELOP DIRS';
cd ${DST_DIR};
ln -s ${CSS_SYM} css;
ln -s ${JS_SYM} js;
ln -s ${IMG_SYM} img;
cd -;
echo '';


# CSS
echo "STARTS THE CREATION OF CSS FILES";
echo '';

cp -R ${SRC_DIR}/css/img ${CSS_DIR}/;
echo "copied ${CSS_DIR}/img/";

cp ${SRC_DIR}/css/bwp.css ${CSS_DIR}/bwp.css;
echo "copied ${CSS_DIR}/bwp.css";

yui-compressor ${CSS_DIR}/bwp.css \
            -o ${CSS_DIR}/bwp.min.css --charset "utf-8";
echo "created ${CSS_DIR}/bwp.min.css";
echo '';

# JS
echo "STARTS THE CREATION OF JS FILES";
echo '';

cp ${SRC_DIR}/js/bwp.js ${JS_DIR}/bwp.js;
echo "copied ${JS_DIR}/bwp.js";

yui-compressor ${JS_DIR}/bwp.js \
            -o ${JS_DIR}/bwp.min.js --charset "utf-8";
echo "created ${JS_DIR}/bwp.min.js";
echo '';

# IMG
echo "STARTS THE COPYING IMAGE FILES";
echo '';

cp -v ${SRC_DIR}/img/*.gif ${IMG_DIR}/;
#~ cp -v ${SRC_DIR}/img/*.jpg ${IMG_DIR}/;
cp -v ${SRC_DIR}/img/*.png ${IMG_DIR}/;
cp -v ${SRC_DIR}/img/*.svg ${IMG_DIR}/;

echo '';

echo "ALL COMPLETED";

exit 0;
