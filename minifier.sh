#!/bin/sh

yui-compressor 'bwp/static_src/css/bwp.css' -o 'bwp/static_src/css/bwp.min.css' --charset 'utf-8'
yui-compressor 'bwp/static_src/js/bwp.js' -o 'bwp/static_src/js/bwp.min.js' --charset 'utf-8'
