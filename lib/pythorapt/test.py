import apt
test = apt.APT('/dev/ttyUSB0')
test.open()
print(test.get_channel())
test.mod_identify()
test.close()
print('test1')
with apt.APT('/dev/ttyUSB0') as r:
    r.mod_identify()
print('test2')
