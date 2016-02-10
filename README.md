# ansible-apicem-dynamic-inventory
With this python script you can use <a href="https://developer.cisco.com/site/apic-em/" target="_blank">Cisco APIC-EM</a> as a dynamic inventory for <a href="https://github.com/ansible/ansible" target="_blank">ansible</a>. <br />
I want to mention that I used code snippets from the project <a href="https://github.com/joelwking/ansible-apic-em" target="_blank">ansible-apic-em</a>, which contains an *APIC-EM ansible module*. <br />
By contrast my project uses APIC-EM as a real dynamic inventory for ansible playbooks.

## usage
1. Place the file *apicem-dynamic-inventory.py* in a folder at your ansible-project. For example the folder can be called "dynamic-inventory".
2. Edit the file and change the variables self.controllername, self.username and self.password to your APIC-EM values.
3. Execute a playbook with APIC-EM as the dynamic inventory.

## examples
The example playbook uses the ansible module *ntc_show_command* of the project <a href="https://github.com/networktocode/ntc-ansible" target="_blank">ntc-ansible</a>. Please consider that you need the module and the **template**-file for the command you are using (in this case **show clock**).

**all devices**
```shell
ansible-playbook regex.yml -i dynamic-inventory
```

**limit to one location** 
```shell
ansible-playbook regex.yml -i dynamic-inventory --limit "mylocation"
```

**limit to one device**
```shell
ansible-playbook regex.yml -i dynamic-inventory --limit "mydevice"
```

## returned variables
In this version the following variables are returned by the dynamic inventory as *host variables*:
* macAddress
* upTime
* bootDateTime
* location
* device_ip
* software

Following versions will also return *platform* as a variable. This would be useful for other ansible-modules like the ones from ntc-ansible.

## miscellaneous
* this version doesnt return devices which have no location set in APIC-EM

## license
This project is published with the <a href="https://opensource.org/licenses/MIT" target="_blank">MIT license</a>. So feel free to use the code in your own projects.
