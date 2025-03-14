

def terraform_template(username, subred_unica, gateway):
 return f"""
terraform {{
  required_version = ">= 0.14.0"
  required_providers {{
    openstack = {{
        source  = "terraform-provider-openstack/openstack"
         version = "~> 1.53.0"
    }}
  }}
}}

# Configurar el provider de openstack
provider "openstack" {{
  user_name   = "terraform"
  tenant_name = "terraform"
  password    = "!Terraform_rsti_2025"
  auth_url    = "http://138.4.21.62:5000/v3/"
  region      = "RegionOne"
}}

# Configuracion de flavours
resource "openstack_compute_flavor_v2" "b5g_terraform_small" {{
  name      = "b5g_terraform_small"
  ram       = 2048
  vcpus     = 1
  disk      = 0
  flavor_id = "101"
  is_public = true
}}

resource "openstack_compute_flavor_v2" "b5g_terraform_medium" {{
  name      = "b5g_terraform_medium"
  ram       = 4096
  vcpus     = 2
  disk      = 0
  flavor_id = "102"
  is_public = true
}}

resource "openstack_compute_flavor_v2" "b5g_terraform_large" {{
  name      = "b5g_terraform_large"
  ram       = 8192
  vcpus     = 4
  disk      = 0
  flavor_id = "103"
  is_public = true
}}

resource "openstack_networking_secgroup_rule_v2" "ssh_rule" {{
  direction         = "ingress"
  ethertype         = "IPv4"
  protocol          = "tcp"
  port_range_min    = 22
  port_range_max    = 22
  remote_ip_prefix  = "0.0.0.0/0"
  security_group_id = "5d30c798-f894-4886-8913-5ba29bfaf740" #Id del grupo de seguridad default
}}

######################
# Configuracion de red del user 
# Creacion de la red interna
resource "openstack_networking_network_v2" "{username}_network" {{
  name           = "{username}_network"
  admin_state_up = true
}}

# Creacion de la subred de control
resource "openstack_networking_subnet_v2" "{username}_control_subnetwork" {{
  name       = "{username}_control_subnetwork"
  network_id = openstack_networking_network_v2.{username}_network.id
  cidr       = "{subred_unica}"
  gateway_ip = "{gateway}"
}}

# Configuracion del router para conectarse a las redes de gestion
resource "openstack_networking_router_v2" "mgmt_router_{username}" {{
  name                = "mgmt_router_{username}"
  admin_state_up      = true
  external_network_id = "30157725-23a0-4b3e-bd6a-ebfc46c39cac" # ID de la red externa
}}

# Conexion del router a la subred de control del user 
resource "openstack_networking_router_interface_v2" "router_internal_interface" {{
  router_id = openstack_networking_router_v2.mgmt_router_{username}.id
  subnet_id = openstack_networking_subnet_v2.{username}_control_subnetwork.id
}}

# Crear IP flotante para el broker 
resource "openstack_networking_floatingip_v2" "floating_ip" {{
  pool = "extnet" # Asigna una IP en el rango de direcciones que tenemos en la red externa
}}

# Asociar la IP flotante a la instancia
resource "openstack_compute_floatingip_associate_v2" "server_floating_ip_assoc" {{
  floating_ip = openstack_networking_floatingip_v2.floating_ip.address
  instance_id = openstack_compute_instance_v2.broker_{username}.id
}}
######################

# Puerto para broker en la subred de control
resource "openstack_networking_port_v2" "broker_control_port" {{
  name       = "broker_control_port"
  network_id = openstack_networking_network_v2.{username}_network.id
  fixed_ip {{
    subnet_id = openstack_networking_subnet_v2.{username}_control_subnetwork.id
  }}
  timeouts {{
    create = "10m"
    delete = "10m"
  }}
}}

# Crear instancia del broker con dos interfaces de red
resource "openstack_compute_instance_v2" "broker_{username}" {{
  name      = "broker_1"
  image_id  = "db02fc5c-cacc-42be-8e5f-90f2db65cf7c"
  flavor_id = openstack_compute_flavor_v2.b5g_terraform_small.id

  network {{
    port = openstack_networking_port_v2.broker_control_port.id
  }}
}}
"""




def append_section_5G(username, subred_unica): 
 return f"""
# Creacion de la subred interna 5G
resource "openstack_networking_subnet_v2" "{username}_5G_subnetwork" {{
  name       = "{username}_5G_subnetwork"
  network_id = openstack_networking_network_v2.{username}_network.id
  cidr       = "{subred_unica}"
}}

# Puerto para UE en la subred de servidores
resource "openstack_networking_port_v2" "{username}_UE_5G_port" {{
  name       = "{username}_UE_5G_port"
  network_id = openstack_networking_network_v2.{username}_network.id
  fixed_ip {{
    subnet_id = openstack_networking_subnet_v2.{username}_5G_subnetwork.id
  }}
  timeouts {{
    create = "10m"
    delete = "10m"
  }}
}}

# Puerto para UE en la subred de control
resource "openstack_networking_port_v2" "{username}_UE_control_port" {{
  name       = "{username}_UE_control_port"
  network_id = openstack_networking_network_v2.{username}_network.id
  fixed_ip {{
    subnet_id = openstack_networking_subnet_v2.{username}_control_subnetwork.id
  }}
  timeouts {{
    create = "10m"
    delete = "10m"
  }}
}}

# Crear instancia del UE
resource "openstack_compute_instance_v2" "{username}_UE" {{
  name      = "{username}_UE"
  image_id  = "db02fc5c-cacc-42be-8e5f-90f2db65cf7c"
  flavor_id = openstack_compute_flavor_v2.b5g_terraform_small.id

  network {{
    port = openstack_networking_port_v2.{username}_UE_5G_port.id
  }}

  network {{
    port = openstack_networking_port_v2.{username}_UE_control_port.id
  }}
}}

#------------

# Puerto para AGF en la subred de servidores
resource "openstack_networking_port_v2" "{username}_AGF_5G_port" {{
  name       = "{username}_AGF_5G_port"
  network_id = openstack_networking_network_v2.{username}_network.id
  fixed_ip {{
    subnet_id = openstack_networking_subnet_v2.{username}_5G_subnetwork.id
  }}
  timeouts {{
    create = "10m"
    delete = "10m"
  }}
}}

# Puerto para AGF en la subred de control
resource "openstack_networking_port_v2" "{username}_AGF_control_port" {{
  name       = "{username}_AGF_control_port"
  network_id = openstack_networking_network_v2.{username}_network.id
  fixed_ip {{
    subnet_id = openstack_networking_subnet_v2.{username}_control_subnetwork.id
  }}
  timeouts {{
    create = "10m"
    delete = "10m"
  }}
}}

# Crear instancia del AGF
resource "openstack_compute_instance_v2" "{username}_AGF" {{
  name      = "{username}_AGF"
  image_id  = "db02fc5c-cacc-42be-8e5f-90f2db65cf7c"
  flavor_id = openstack_compute_flavor_v2.b5g_terraform_small.id

  network {{
    port = openstack_networking_port_v2.{username}_AGF_5G_port.id
  }}

  network {{
    port = openstack_networking_port_v2.{username}_AGF_control_port.id
  }}
}}

#------------

# Puerto para core5G en la subred de servidores
resource "openstack_networking_port_v2" "{username}_core5G_5G_port" {{
  name       = "{username}_core5G_5G_port"
  network_id = openstack_networking_network_v2.{username}_network.id
  fixed_ip {{
    subnet_id = openstack_networking_subnet_v2.{username}_5G_subnetwork.id
  }}
  timeouts {{
    create = "10m"
    delete = "10m"
  }}
}}

# Puerto para core5G en la subred de control
resource "openstack_networking_port_v2" "{username}_core5G_control_port" {{
  name       = "{username}_core5G_control_port"
  network_id = openstack_networking_network_v2.{username}_network.id
  fixed_ip {{
    subnet_id = openstack_networking_subnet_v2.{username}_control_subnetwork.id
  }}
  timeouts {{
    create = "10m"
    delete = "10m"
  }}
}}

# Crear instancia del core5G
resource "openstack_compute_instance_v2" "{username}_AGF" {{
  name      = "{username}_core5G"
  image_id  = "db02fc5c-cacc-42be-8e5f-90f2db65cf7c"
  flavor_id = openstack_compute_flavor_v2.b5g_terraform_small.id

  network {{
    port = openstack_networking_port_v2.{username}_core5G_5G_port.id
  }}

  network {{
    port = openstack_networking_port_v2.{username}_core5G_control_port.id
  }}
}}
    """

