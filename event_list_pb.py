#!/usr/bin/env python3
import sys
import os
import json
import glob
from datetime import datetime, timedelta, timezone

from protobuftext_decoder import ProtobufDecoder


BASENAME="alert_events.txt"
def js_list( ):
    patharray = [ \
                 "./" + BASENAME, \
                 "./alerts" + BASENAME, \
                 "./cvm_logs/alerts/" + BASENAME, \
                 ] \
              + glob.glob("./*-CW-logs/cvm_logs/alerts/"+ BASENAME ) \
              + glob.glob("./*logs//cvm_logs/alerts/" + BASENAME  ) 

    a = []
    ProtobufDecoder.setRepeatedKeys( [ "params", "classification_list" ] )
    pb = ProtobufDecoder()

    for fn in  patharray :
        ##print("fn = %s" % fn )
        if ( not os.path.isfile( fn ) )  :
            continue

        if ( 0 == os.path.getsize( fn ) ) :
            print( "### %s found but empty ###" % fn, file=sys.stderr )
            continue

        try:
            a = pb.load( open( fn, "r" ) )

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

#    flag_searchfiles = False
#    flag_list = True
    arglen = len( sys.argv ) 

    alerts_data = js_list()

    if( alerts_data is None ):
        print( BASENAME +" file not found.", file=sys.stderr )
        sys.exit(1) 

    if( len( alerts_data ) < 1 ):
        print( "alerts.txt file not found.", file=sys.stderr )
        sys.exit(1) 

    JST = timezone(timedelta(hours=+9), 'JST')
    UTC = timezone.utc


    ## list alerts
    if( arglen < 2 ):

            for e in alerts_data : 
    
                msg = replace_string_params( e["default_msg"] , e["params"] ) 
                st =  datetime.fromtimestamp( int( e["creation_timestamp_usecs"] )/ 1000000, JST ).strftime("%Y-%m-%d %H:%M:%S (%Z)" )

                print( "%25s , %s , %s , %s" % ( st, e["uuid"], e["alert_uid"], msg ) )

            print("")

    ## detailsalerts
    else:
            for e in alerts_data :

                if( e["uuid"] == sys.argv[1] ):


                    create_time_sec =  int( e["creation_timestamp_usecs"] ) / 1000000
                    st  = datetime.fromtimestamp( create_time_sec, JST ).strftime("%Y-%m-%d %H:%M:%S (%Z)" )  
                    stu = datetime.fromtimestamp( create_time_sec, UTC ).strftime("%Y-%m-%d %H:%M:%S (%Z)" )

                    browser_info = None
                    if "params" in e :
                        for p in e["params"] :
                           if p["member_name"] == "browser_info" :
                               browser_info = p["member_value"]["string_value"]

                    print("")
                    print( "ID                        : %s" % e["uuid"] )
                    print( "Alert Type                : %s" % e["alert_uid"] )
                    print( "Classifications           : %s" % e["classification_list"] )
                    print( "Message                   : %s" % ( replace_string_params( e["default_msg"] , e["params"] ) ) )
                    if browser_info :
                        print( "Browser Info              : %s" % browser_info )
                    print( "Serverity                 : %s" % e["severity"] )
                    if "originating_cluster_uuid" in e:
                        print( "Original Cluster UUID     : %s" % e["originating_cluster_uuid"] )
                    print( "Created On                : %s  --  %s" % ( st, stu ) )

                    if( "affected_entities" in e ):
                        for ae in e["affected_entities"] :
                            print( "Entities On               : %s:%s ( %s )" % ( ae["entity_type_display_name"], ae["uuid"], ae["entity_name"] ) )
                    print("")

    sys.exit(0) 

if __name__ == '__main__' :
    main()
