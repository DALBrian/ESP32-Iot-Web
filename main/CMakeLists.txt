idf_component_register(SRCS "main.c"
                       REQUIRES 
                       protocol_examples_common   
                       mqtt 
                       nvs_flash 
                       esp_netif 
                       dht22_lib
                       INCLUDE_DIRS ".")
