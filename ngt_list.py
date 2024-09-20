#!/usr/bin/env python3
import sys
import os
import json
import glob
import re
from datetime import datetime, timedelta, timezone

from protobuftext_decoder import ProtobufDecoder


BASENAME="nutanix_guest_tools_cli.txt"

def pb_list( ):
    patharray = [ \
                 "./" + BASENAME, \
                 "./cvm_config/" + BASENAME, \
                 ] \
              + glob.glob("./*-CW-logs/cvm_config/"+ BASENAME ) \
              + glob.glob("./*logs//cvm_config/" + BASENAME  ) 

    a = []
    ProtobufDecoder.setRepeatedKeys( [ "vm_uuid_vec", "vm_info_vec" ] )
    pb = ProtobufDecoder()

    for fn in  patharray :
        ##print("fn = %s" % fn )
        if ( not os.path.isfile( fn ) )  :
            continue

        if ( 0 == os.path.getsize( fn ) ) :
            print( "### %s found but empty ###" % fn, file=sys.stderr )
            continue

        try:
            with open( fn, "r" ) as f:
                s = re.split(r'\n\[std...\]:\n', f.read() )
                ## s[0] = [logbay]...
                ## ---- ^[stdout]:$ ----------
                ## s[1] = stdout outputs
                ## ---- ^[stderr]:$ ----------
                ## s[2] = stderr outputs

            a = pb.dumps( s[1] )

        except FileNotFoundError:
            continue

        if( len( a ) > 0 ):
            print( "### %s ###" % fn, file=sys.stderr )
            return a 

    return None


def replace_string( bstr, context_types, context_values ):
    s = bstr
    for i in range( 0, len( context_types ) ):
        s = s.replace( "{%s}" % ( context_types[ i ] ), context_values[ i ] ) 
    return s

def replace_string_params( bstr, params_array ):

    s = bstr
    for p in  params_array :
        if( "string_value" in p["member_value"] ):
            s = s.replace( "{%s}" % ( p["member_name"] ),p["member_value"]["string_value"] ) 
        elif( "int64_value" in p["member_value"] ):
            s = s.replace( "{%s}" % ( p["member_name"] ),str( p["member_value"]["int64_value"] ) ) 

    return s


def main():
    print( "defaultencoding: %s"% sys.getdefaultencoding() )

#    flag_searchfiles = False
#    flag_list = True

    ngt_data  = pb_list()

    if( ngt_data is None ):
        print( BASENAME +" file not found.", file=sys.stderr )
        sys.exit(1) 

    JST = timezone(timedelta(hours=+9), 'JST')
    UTC = timezone.utc

    if "vm_info_vec" in ngt_data :

        ## list ngts
        if len( sys.argv ) < 2 :
            for e in ngt_data["vm_info_vec"] :

                print("VM Id:             : %s" % e["vm_uuid"] )
                print("VM Name            : %s" % e["vm_name"] )   
                print("NGT Enabled        : %s" % e["guest_tools_enabled"] )   
                print("Tools ISO Mounted  : %s" % e["tools_mounted"] )   
                print("VSS Snapshot       : %s" % e["capabilities"]["vss_snapshot"] )   
                print("File Level Restore : %s" % e["capabilities"]["file_level_restore"] )   
                print("Communication Link Active : %s" % e["communication_link_active"] )   
                print("")

        ## RAW mode ##
        elif sys.argv[1] == "RAW" :
            print( "### RAW MODE ####", file=sys.stderr )
            print( json.dumps( ngt_data, indent=4 ) )

        ## NGT details
        else:
            for e in ngt_data["vm_info_vec"] :
                if e["vm_uuid"] == sys.argv[1] :    
            
                    print("NGT UUID                  : %s" % e["ngt_uuid"] )   
                    ##print("System UUID               : %s" % e["system_uuid"] )   
                    print("VM Id:                    : %s" % e["vm_uuid"] )
                    print("VM Name                   : %s" % e["vm_name"] )   

                    print("NGT Feature:")
                    print("  NGT Enabled             : %s" % e["guest_tools_enabled"] )   
                    print("  Tools ISO Mounted       : %s" % e["tools_mounted"] )   
                    print("  VSS Snapshot            : %s" % e["capabilities"]["vss_snapshot"] )   
                    print("  File Level Restore      : %s" % e["capabilities"]["file_level_restore"] )   

                    print("Communication Link Info:")
                    print("  Communication Link Type   : %s" % e["communication_type"] )   
                    print("  Communication Link Active : %s" % e["communication_link_active"] )   
                    print("  Serial Link Active        : %s" % e["communication_link_over_serial_port_active"] )   

                    if ( "vm_info" in e ) and ( len( e["vm_info"] ) > 0 ):
                        v = e["vm_info"]
                        print("VM Info:" )   
                        print("  NGT version on Guest    : %s" % v["ngt_version"] )   
                        print("  guestOS Type/Release    : %s ( %s )" % ( v["guest_os_type"], v["guest_os_release"] ) )
                        print("  guestOS Version         : %s" % ( v["guest_os_version"] ) )
                        print("  Is Windows Server       : %s" % ( v["is_windows_server_os"] ) )
                        print("  64bit OS                : %s" % ( v["is_64_bit"] ) )
                        print("  NGT install completed   : %s" % ( v["is_installation_complete"] ) )
                        print("  VSS installed           : %s" % ( v["vss_installed"] ) )
                        print("  Scripts installed       : %s" % ( v["backup_scripts_installed"] ) )

                        if "timezone_info" in v :
                            print("Timezone Info:" )   
                            print("  Timezone                : %s" % v["timezone_info"]["os_timezone"] )
                            print("  HW clock is UTC         : %s" % v["timezone_info"]["real_time_is_universal"] )


                        print("Network Info:" )   
                        if "network_interfaces_info" in v :
                            n = v["network_interfaces_info"]
                            print("  Device Driver           : %s" % n["interface"] )   
                            print("  MAC address             : %s" % n["mac_address"] )   
   
                            if n["ipv4_info_vec"]["is_static_ip"] :
                                st = "static"
                            else:
                                st = "dynamic"

                            print("  IP address              : %s/%s ( %s )" % ( n["ipv4_info_vec"]["ip_address"], n["ipv4_info_vec"]["prefix_length"], st ) )
                            print("  Default Gateway         : %s" % n["ipv4_info_vec"]["gateway_ip_vec"] )   
                            print("  DNS servers             : %s" % ", ".join( n["dns_ip_vec"] ) ) 
                        else:
                            print(" (nothing)" )   

                        print("Client Certiticates:")
                        print("  Client Cert generated   : %s" % e["client_certificates_generated"] )
                        if "client_cert_expiry_date" in v :
                            rt  =  datetime.fromtimestamp( int( v["client_cert_expiry_date"] ), JST).strftime("%Y-%m-%d %H:%M:%S (%Z)")
                            rtu =  datetime.fromtimestamp( int( v["client_cert_expiry_date"] ), UTC).strftime("%Y-%m-%d %H:%M:%S (%Z)") 
                            print("  Cert expire date        : %s -- %s" % ( rt, rtu ) )
                    else:
                        print("VM Info: (nothing)" )   

                    print("")
                ## for loop
            ## modes    
        ## arglen
    ## if
    sys.exit(0) 

if __name__ == '__main__' :
    main()
