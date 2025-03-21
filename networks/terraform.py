def terraform_template(username, password, subred_control, gateway):
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
  cidr       = "{subred_control}"
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
  name      = "broker_{username}"
  image_id  = "db02fc5c-cacc-42be-8e5f-90f2db65cf7c"
  flavor_id = "101"
  user_data = <<-EOF
              #!/bin/bash
              # Deshabilitar el acceso SSH para el usuario root
              echo "PermitRootLogin no" >> /etc/ssh/sshd_config
              
              # Crear un nuevo usuario
              useradd -m {username}
              
              # Establecer la contrasena para el nuevo usuario (puedes cambiarla)
              echo "{username}:{password}" | chpasswd
              usermod -aG sudo {username}

              # Asegurarse de que el usuario pueda acceder a traves de SSH
              echo "PasswordAuthentication yes" >> /etc/ssh/sshd_config
              echo "AllowUsers {username}" >> /etc/ssh/sshd_config

              # Reiniciar el servicio SSH para que los cambios tomen efecto
              systemctl restart sshd
              EOF

network {{
    port = openstack_networking_port_v2.broker_control_port.id
  }}

}}
"""


def append_section_5G(username, password, subred_control, subred_UE_AGF, subred_AGF_core5G, subred_core5G_internet, gateway): 
 return f"""

# subred_UE_AGF = {subred_UE_AGF}
# subred_AGF_core5G = {subred_AGF_core5G}
# subred_core5G_internet = {subred_core5G_internet}


# Creacion de la subred 5G UE_AGF
resource "openstack_networking_subnet_v2" "{username}_UE_AGF_subnetwork" {{
  name       = "{username}_UE_AGF_subnetwork"
  network_id = openstack_networking_network_v2.{username}_network.id
  cidr       = "{subred_UE_AGF}"

}}

# Creacion de la subred 5G AGF_core5G
resource "openstack_networking_subnet_v2" "{username}_AGF_core5G_subnetwork" {{
  name       = "{username}_AGF_core5G_subnetwork"
  network_id = openstack_networking_network_v2.{username}_network.id
  cidr       = "{subred_AGF_core5G}"
}}

# Creacion de la subred 5G core5G_internet
resource "openstack_networking_subnet_v2" "{username}_core5G_internet_subnetwork" {{
  name       = "{username}_core5G_internet_subnetwork"
  network_id = openstack_networking_network_v2.{username}_network.id
  cidr       = "{subred_core5G_internet}"
  gateway_ip = "{gateway}"
}}


# Puerto para UE en la subred UE_AGF
resource "openstack_networking_port_v2" "{username}_UE_AGF_port" {{
  name       = "{username}_UE_AGF_port"
  network_id = openstack_networking_network_v2.{username}_network.id
  fixed_ip {{
    subnet_id = openstack_networking_subnet_v2.{username}_UE_AGF_subnetwork.id
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
  flavor_id = "101"
  user_data = <<-EOF
              # Obtener las IP fijas de los puertos de Terraform
              AGF_IP=${{openstack_networking_port_v2.{username}_UE_AGF_port.fixed_ip[0].ip_address}}
              CONTROL_IP=${{openstack_networking_port_v2.{username}_UE_control_port.fixed_ip[0].ip_address}}

              # Anadir las rutas con metricas
              ip route add {subred_UE_AGF} via $AGF_IP dev ens3 metric 200
              ip route add {subred_control} via $CONTROL_IP dev ens4 metric 300
              
              sudo systemctl restart systemd-networkd
              EOF
  network {{
    port = openstack_networking_port_v2.{username}_UE_AGF_port.id
  }}

  network {{
    port = openstack_networking_port_v2.{username}_UE_control_port.id
  }}
  depends_on = [
    openstack_networking_port_v2.{username}_UE_AGF_port,
    openstack_networking_port_v2.{username}_UE_control_port
  ]
}}

#------------

# Puerto para AGF en la subred UE_AGF
resource "openstack_networking_port_v2" "{username}_AGF_UE_port" {{
  name       = "{username}_AGF_UE_port"
  network_id = openstack_networking_network_v2.{username}_network.id
  fixed_ip {{
    subnet_id = openstack_networking_subnet_v2.{username}_UE_AGF_subnetwork.id
  }}
  timeouts {{
    create = "10m"
    delete = "10m"
  }}
}}

# Puerto para AGF en la subred AGF_core5G
resource "openstack_networking_port_v2" "{username}_AGF_core5G_port" {{
  name       = "{username}_AGF_core5G_port"
  network_id = openstack_networking_network_v2.{username}_network.id
  fixed_ip {{
    subnet_id = openstack_networking_subnet_v2.{username}_AGF_core5G_subnetwork.id
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
  flavor_id = "101"
  user_data = <<-EOF            
              # Obtener las IP fijas de los puertos de Terraform
              UE_IP=${{openstack_networking_port_v2.{username}_UE_AGF_port.fixed_ip[0].ip_address}}
              CONTROL_IP=${{openstack_networking_port_v2.{username}_AGF_control_port.fixed_ip[0].ip_address}}
              CORE_IP=${{openstack_networking_port_v2.{username}_AGF_core5G_port.fixed_ip[0].ip_address}}

              # Anadir las rutas con metricas
              ip route add {subred_AGF_core5G} via $CORE_IP dev ens3 metric 50
              ip route add {subred_UE_AGF} via $UE_IP dev ens4 metric 50
              ip route add {subred_control} via $CONTROL_IP dev ens5 metric 50
              
              sudo systemctl restart systemd-networkd
              EOF
  network {{
    port = openstack_networking_port_v2.{username}_AGF_UE_port.id
  }}

  network {{
    port = openstack_networking_port_v2.{username}_AGF_core5G_port.id
  }}

  network {{
    port = openstack_networking_port_v2.{username}_AGF_control_port.id
  }}
}}

#------------

# Puerto para core5G en la subred AGF_core5G
resource "openstack_networking_port_v2" "{username}_core5G_AGF_port" {{
  name       = "{username}_core5G_AGF_port"
  network_id = openstack_networking_network_v2.{username}_network.id
  fixed_ip {{
    subnet_id = openstack_networking_subnet_v2.{username}_AGF_core5G_subnetwork.id
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

# Puerto para core5G en la subred de internet
resource "openstack_networking_port_v2" "{username}_core5G_internet_port" {{
  name       = "{username}_core5G_internet_port"
  network_id = openstack_networking_network_v2.{username}_network.id
  fixed_ip {{
    subnet_id = openstack_networking_subnet_v2.{username}_core5G_internet_subnetwork.id
  }}
  timeouts {{
    create = "10m"
    delete = "10m"
  }}
}}

# Crear instancia del core5G
resource "openstack_compute_instance_v2" "{username}_core5G" {{
  name      = "{username}_core5G"
  image_id  = "db02fc5c-cacc-42be-8e5f-90f2db65cf7c"
  flavor_id = "101"
  user_data = <<-EOF
              # Obtener las IP fijas de los puertos de Terraform
              AGF_IP=${{openstack_networking_port_v2.{username}_core5G_AGF_port.fixed_ip[0].ip_address}}
              CONTROL_IP=${{openstack_networking_port_v2.{username}_core5G_control_port.fixed_ip[0].ip_address}}
              INTERNET_IP=${{openstack_networking_port_v2.{username}_core5G_internet_port.fixed_ip[0].ip_address}}

              # Anadir las rutas con metricas
              ip route add {subred_core5G_internet} via $INTERNET_IP dev ens3 metric 50
              ip route add {subred_AGF_core5G} via $AGF_IP dev ens4 metric 50
              ip route add {subred_control} via $CONTROL_IP dev ens5 metric 50
              
              sudo systemctl restart systemd-networkd
              EOF
  network {{
    port = openstack_networking_port_v2.{username}_core5G_internet_port.id
  }}
  network {{
    port = openstack_networking_port_v2.{username}_core5G_AGF_port.id
  }}
  network {{
    port = openstack_networking_port_v2.{username}_core5G_control_port.id
  }}
}}

# # Configuracion del router para conectarse a internet
# resource "openstack_networking_router_v2" "mgmt_router_core5G_{username}" {{
#   name                = "mgmt_router_core5G_{username}"
#   admin_state_up      = true
#   external_network_id = "30157725-23a0-4b3e-bd6a-ebfc46c39cac" # ID de la red externa
# }}

# # Conexion del router a la red de internet 
# resource "openstack_networking_router_interface_v2" "router_internal_interface_core" {{
#   router_id = openstack_networking_router_v2.mgmt_router_core5G_{username}.id
#   subnet_id = openstack_networking_subnet_v2.{username}_core5G_internet_subnetwork.id
# }}

# # Crear IP flotante para el core5G
# resource "openstack_networking_floatingip_v2" "floating_ip_core" {{
#   pool = "extnet" # Asigna una IP en el rango de direcciones que tenemos en la red externa
# }}

# # Asociar la IP flotante a la instancia
# resource "openstack_compute_floatingip_associate_v2" "server_floating_ip_assoc_core" {{
#   floating_ip = openstack_networking_floatingip_v2.floating_ip_core.address
#   instance_id = openstack_compute_instance_v2.core5G_{username}.id
#}}
"""
