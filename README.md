A BIG-IQ license manager can import base regkeys into a regkey pool and activate them. It cannot import addon keys from a csv along with the base regkey or use a csv to install addon keys to previously Activated offerings. Doing a large number of these one at a time in the GUI can be time-consuming. This script makes it possible to feed the keys as arguments when running the script. It only installs one license at a time but makes it possible to loop over a file(s) to automate the process.

This script can be used to install base regkeys with or without the addonkeys. It can also install addon keys to an existing offering. It cannot be run locally on a BIG-IQ because some modules are not available for import.

./reg_pool_tool.py -h
usage: reg_pool_tool.py [-h] [-d] [-v] [-a ADDRESS] [-u USERNAME]
                        [-p PASSWORD] [-l] [-o POOL_UUID] [-r REG_KEY]
                        [-A ADD_ON_KEY_LIST] [-i INSTALL_POOL_UUID]
                        [-m MODIFY_POOL_UUID]

This is a tool for workingwith regkey pool on BIG-IQ

optional arguments:
  -h, --help            show this help message and exit
  -d, --debug           enable debug
  -v, --verbose         enable verbose for options that have it
  -a ADDRESS, --address ADDRESS
                        IP address of the target host
  -u USERNAME, --username USERNAME
                        username for auth to host
  -p PASSWORD, --password PASSWORD
                        password for auth to host
  -l, --list-pools      list the UUIDs for existing regkey pools, requires no
                        args
  -o POOL_UUID, --offerings POOL_UUID
                        take UUID of pool as arg and list the offerings for a
                        pool use -v to also show the active modules
  -r REG_KEY, --regkey REG_KEY
                        takes and stores the regkey for use in other options
  -A ADD_ON_KEY_LIST, --add-on-keys ADD_ON_KEY_LIST
                        takes string of comma sep addon keys for use by other
                        options
  -i INSTALL_POOL_UUID, --install-offering INSTALL_POOL_UUID
                        takes pool UUID as arg and installs new
                        offering,requires -r, -A can be used to install addon
                        keys atthe same time
  -m MODIFY_POOL_UUID, --modify-offering-addons MODIFY_POOL_UUID
                        takes pool UUID as arg and installs addon to
                        offering,requires -A [addon_key_list] and -r reg_key
Examples:

List regkey pools:

./reg_pool_tool.py -a 192.0.44 -l
List the offerings in a regkey pool:

./reg_pool_tool.py -a 192.0.2.44 -o 07c77c7f-3170-4b17-93de-31e4f39e4709 
Installing a new regkey with addon:

./reg_pool_tool.py -a 192.0.2.44 -i 5678d528-daac-4430-a87e-b67b87acfe20 -r B6083-41023-70161-19033-9429393 -A X792747-5616417
Modifying an existing offering adding a new addon key:

./reg_pool_tool.py -a 192.0.2.44 -m 5678d528-daac-4430-a87e-b67b87acfe20 -r K1260-99690-76028-13047-3993585 -A X792747-5616417
