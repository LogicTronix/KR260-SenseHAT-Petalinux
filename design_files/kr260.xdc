#RPi IIC
set_property PACKAGE_PIN AE15 [get_ports {iic_sda_io}]
set_property IOSTANDARD LVCMOS33 [get_ports {iic_sda_io}]
set_property PULLUP true [get_ports {iic_sda_io}]

set_property PACKAGE_PIN AE14 [get_ports {iic_scl_io}]
set_property IOSTANDARD LVCMOS33 [get_ports {iic_scl_io}]
set_property PULLUP true [get_ports {iic_scl_io}]

set_property PACKAGE_PIN AA12 [get_ports {rpi_irpt_tri_i}]
set_property IOSTANDARD LVCMOS33 [get_ports {rpi_irpt_tri_i}]
