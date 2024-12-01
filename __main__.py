"""An Azure RM Python Pulumi program"""

import pulumi
from pulumi_azure_native import storage
from pulumi_azure_native import resources
from pulumi_azure_native import network
from pulumi_azure_native import compute

# Pulumi-Konfiguration
# Einstellungen für die Festplattengröße und den Festplattentyp definieren (lt. Monograph)
config = pulumi.Config()
disk_size = config.get_int("diskSize") or 1024  # Standardgröße: 1024 GB
disk_sku = config.get("diskSku") or "Premium_LRS"  # Standard-SKU: Premium_LRS

# Erstellen einer Resource Group
# Eine Resource Group ist ein Container für alle Ressourcen in Azure
resource_group = resources.ResourceGroup("resourceGroup")

# Erstellen eines Virtual Networks und eines Subnetzes
# Ein Virtual Network (VNet) bietet eine private Netzwerkumgebung für die VMs.
vnet = network.VirtualNetwork(
    "vnet",
    resource_group_name=resource_group.name,
    address_space=network.AddressSpaceArgs(
        address_prefixes=["10.0.0.0/16"]  # Das gesamte Netzwerk verwendet diesen Adressbereich.
    )
)

# Subnetz: Ein Bereich innerhalb des virtuellen Netzwerks.
subnet = network.Subnet(
    "subnet",
    resource_group_name=resource_group.name,
    virtual_network_name=vnet.name,
    address_prefix="10.0.1.0/24"  # Subnetz mit spezifischem Adressbereich
)

# Erstellen von Netzwerkadaptern für die virtuellen Maschinen
# Netzwerkadapter (NIC) verbinden die VMs mit dem Subnetz.
nic1 = network.NetworkInterface(
    "nic1",
    resource_group_name=resource_group.name,
    ip_configurations=[
        network.NetworkInterfaceIPConfigurationArgs(
            name="ipconfig1",
            subnet=network.SubnetArgs(id=subnet.id),
            private_ip_allocation_method="Dynamic",  # IP-Adresse wird automatisch zugewiesen
        )
    ],
)

nic2 = network.NetworkInterface(
    "nic2",
    resource_group_name=resource_group.name,
    ip_configurations=[
        network.NetworkInterfaceIPConfigurationArgs(
            name="ipconfig2",
            subnet=network.SubnetArgs(id=subnet.id),
            private_ip_allocation_method="Dynamic",
        )
    ],
)

# Erstellen von verwalteten Festplatten
# Zwei leere verwaltete Festplatten (Managed Disks) werden erstellt und konfiguriert.
disk1 = compute.Disk(
    "disk1",
    resource_group_name=resource_group.name,
    disk_size_gb=disk_size,  # Die Größe der Festplatte wird hier definiert
    sku=compute.DiskSkuArgs(name=disk_sku),  # Typ der Festplatte (z. B. Premium_LRS)
    creation_data=compute.CreationDataArgs(create_option="Empty"),  # Leere Festplatte
)

disk2 = compute.Disk(
    "disk2",
    resource_group_name=resource_group.name,
    disk_size_gb=disk_size,
    sku=compute.DiskSkuArgs(name=disk_sku),
    creation_data=compute.CreationDataArgs(create_option="Empty"),
)

# Erstellen von virtuellen Maschinen und Anhängen von Festplatten
# VM1 wird erstellt und die erste Festplatte wird angehängt.
vm1 = compute.VirtualMachine(
    "vm1",
    resource_group_name=resource_group.name,
    network_profile=compute.NetworkProfileArgs(
        network_interfaces=[
            compute.NetworkInterfaceReferenceArgs(id=nic1.id)
        ]
    ),
    hardware_profile=compute.HardwareProfileArgs(
        vm_size="Standard_DS1_v2",  # Die Größe der virtuellen Maschine
    ),
    storage_profile=compute.StorageProfileArgs(
        os_disk=compute.OSDiskArgs(
            create_option="FromImage",  # OS-Disk wird aus einem Image erstellt
            managed_disk=compute.ManagedDiskParametersArgs(
                storage_account_type="Premium_LRS",
            ),
        ),
        image_reference=compute.ImageReferenceArgs(
            publisher="Canonical",  # Ubuntu-Image von Canonical
            offer="UbuntuServer",
            sku="18.04-LTS",
            version="latest",
        ),
        data_disks=[
            compute.DataDiskArgs(
                lun=0,  # Logical Unit Number für die Festplatte
                create_option="Attach",  # Existierende Festplatte anhängen
                managed_disk=compute.ManagedDiskParametersArgs(id=disk1.id),
            )
        ],
    ),
    os_profile=compute.OSProfileArgs(
        computer_name="vm1",  # Hostname der virtuellen Maschine
        admin_username="adminuser",  # Benutzername für den Administrator
        admin_password="P@ssw0rd1234!",  # Passwort (aus Sicherheitsgründen in Produktion vermeiden)
    ),
)

# VM2 wird erstellt und die zweite Festplatte wird angehängt.
vm2 = compute.VirtualMachine(
    "vm2",
    resource_group_name=resource_group.name,
    network_profile=compute.NetworkProfileArgs(
        network_interfaces=[
            compute.NetworkInterfaceReferenceArgs(id=nic2.id)
        ]
    ),
    hardware_profile=compute.HardwareProfileArgs(
        vm_size="Standard_DS1_v2",
    ),
    storage_profile=compute.StorageProfileArgs(
        os_disk=compute.OSDiskArgs(
            create_option="FromImage",
            managed_disk=compute.ManagedDiskParametersArgs(
                storage_account_type="Premium_LRS",
            ),
        ),
        image_reference=compute.ImageReferenceArgs(
            publisher="Canonical",
            offer="UbuntuServer",
            sku="18.04-LTS",
            version="latest",
        ),
        data_disks=[
            compute.DataDiskArgs(
                lun=0,
                create_option="Attach",
                managed_disk=compute.ManagedDiskParametersArgs(id=disk2.id),
            )
        ],
    ),
    os_profile=compute.OSProfileArgs(
        computer_name="vm2",
        admin_username="adminuser",
        admin_password="P@ssw0rd1234!",
    ),
)

# Exportieren der Ressourceninformationen
# Informationen über die Ressourcen werden nach dem Deployment ausgegeben.
pulumi.export("resource_group_name", resource_group.name)
pulumi.export("vnet_name", vnet.name)
pulumi.export("subnet_name", subnet.name)
pulumi.export("vm1_name", vm1.name)
pulumi.export("vm2_name", vm2.name)
pulumi.export("disk1_id", disk1.id)
pulumi.export("disk2_id", disk2.id)