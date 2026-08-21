docker run -v `dirname $0 | pwd`/../../samples/configs:/app/conf/runners -v `dirname $0 | pwd`/../../samples/scripts:/app/samples/scripts  -p 5000:5000  script-server
