set os=createobject("wscript.shell")
do
wscript.sleep 1000*10
os.run "c:\bat\ip.bat",vbhide
loop   