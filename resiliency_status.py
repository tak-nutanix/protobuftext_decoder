#!/usr/bin/env python3
import sys
import os
import json
import glob
import re
from datetime import datetime, timedelta, timezone

from protobuftext_decoder import ProtobufDecoder


BASENAME="zeus_config.txt"

def pb_list( ):
    patharray = [ \
                 "./" + BASENAME, \
                 "./cvm_config/" + BASENAME, \
                 ] \
              + glob.glob("./*-CW-logs/cvm_config/"+ BASENAME ) \
              + glob.glob("./*logs//cvm_config/" + BASENAME  ) 

    a = []
    ProtobufDecoder.setRepeatedKeys( [ "storage_tier_list", "disk_list", "node_list","external_repository_list", 
                                       "reason_for_maintenance_mode_list","container_list","management_server_list", 
                                       "ntp_server_list","name_server_ip_list","rackable_unit_list","vstore_list",
                                       "ssh_key_list","disk_tombstone_list","components","domains","modules","remote_site_list" ] )
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
            if len( s ) > 2 :
                a = pb.dumps( s[1] )
            else:
                a = pb.dumps( s[0] )

        except FileNotFoundError:
            continue

        ##print( json.dumps( a, indent=4 ) )
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

dname = {
    "kZookeeperInstances"   : "ZOOKEEPER",
    "kStaticConfig"         : "STATIC_CONFIGURATION",
    "kCassandraRing"        : "METADATA" ,
    "kFreeSpace"            : "FREE_SPACE",
    "kStargateHealth"       : "STARGATE_HEALTH", 
    "kExtentGroupReplicas"  : "EXTENT_GROUPS", 
    "kOplogEpisodes"        : "OPLOG",
    "kErasureCodeStripSize" : "ERASURE_CODE_STRIP_SIZE"
    }

tname = {
    "kNode" : "NODE",
    "kRackableUnit" : "RACKABLE_UNIT", 
    "kRack" : "RACK", 
    "kDisk" : "DISK" 
}


##
## domain : NODE, RACKABLE_UNIT, DISK
##
def main():
    zeus_data  = pb_list()

    if( zeus_data is None ):
        print( BASENAME +" file not found.", file=sys.stderr )
        sys.exit(1) 

    JST = timezone(timedelta(hours=+9), 'JST')
    UTC = timezone.utc

    if "domain_fault_tolerance_state" in zeus_data:

        ## list ngts
        if len( sys.argv ) < 2 :
            dt = "kNode"

        elif sys.argv[1].lower() == "disk" :
            dt = "kDisk"
        elif sys.argv[1].lower() == "rackable_unit" :
            dt = "kRackableUnit"
        elif sys.argv[1].lower() == "kDisk" :
            dt = "kDisk"

        elif sys.argv[1].lower() == "raw" or  sys.argv[1].lower() == "json" :
            print( "### RAW MODE ####", file=sys.stderr )
            print( json.dumps( zeus_data["domain_fault_tolerance_state"], indent=4 ) )
            exit(0)
        
        for d in zeus_data["domain_fault_tolerance_state"]["domains"] :

            if d["domain_type"] == dt :
                print("")

                domain_type = tname[ d["domain_type"] ]
                if "components" in d :
                    for c in d["components"] :
                        print("Domain Type             : %s" % domain_type )
                        print("Component Type          : %s" % dname[ c["component_type"] ] )
                        print("Current Fault Tolerance : %s" % c["max_faults_tolerated"] )
                        ## print("Fault Tolerance Details : %s" % c["tolerance_details_message"]["message_id"] )
                        print("Fault Tolerance Details : " )

                        rt  =  datetime.fromtimestamp( int( c["last_update_secs"] ), JST).strftime("%Y-%m-%d %H:%M:%S (%Z)")
                        rtu =  datetime.fromtimestamp( int( c["last_update_secs"] ), UTC).strftime("%Y-%m-%d %H:%M:%S (%Z)") 
                        print("Last Update Time        : %s -- %s" % ( rt, rtu ) )
                        print("")
                   
                    ## for loop
                ## if component
            ## domain_type
        ## for d
    ## if
    sys.exit(0) 

if __name__ == '__main__' :
    main()
