#!/usr/bin/env python3
import os,sys
import json


###
### protobuf text decoder
###
class ProtobufDecoder:

    class Debug :
        LEXER_ALL     = 0xf0

        LEXER_DETAIL  = 0x40
        LEXER_TOKEN   = 0x20
        LEXER_INFO    = 0x10

        PARSER_ALL    = 0x0e
        PARSER_DETAIL = 0x08
        PARSER_TOKEN  = 0x04

        METHOD_CALLING = 0x01

        debuglevel = 0x00

        @classmethod
        def setLevel( cls, num ):
            cls.debuglevel = num

        @classmethod
        def printmsg( cls, lv, msg , a=None ):
            if( lv & cls.debuglevel ):

                prefix = " " * int( (lv/2)+2 ) + "Debug: "
                if( a is None ): 
                    print( prefix + str( msg ) )

                else:
                    strs = []
                    if len( a ) > 0 :
                        for t in a :
                            if( ProtobufDecoder.TOK_TYPE in t ):
                                if( t[ProtobufDecoder.TOK_TYPE] == ProtobufDecoder.TYPE_STRING ):
                                    strs.append( t[ProtobufDecoder.TOK_VALUE] )
                                else:
                                    strs.append( t[ProtobufDecoder.TOK_TYPE] )
                            else:
                                strs.append( "??? %s" % t )
                        print( prefix + msg + " [[ " + ", ".join(strs) + " ]]" )
                    else:
                        print( prefix + msg + " [[ (nothing) ]]" )
                        


    TOK_TYPE="type"
    TOK_VALUE="value"
    TYPE_STRING = "string"
    TYPE_COLON = "COLON:"
    TYPE_START = "START<"
    TYPE_END   = ">END"
    TYPE_EOF_MARKER = "__EOF__"


    class SyntaxErrorException( Exception ):
        pass

    REPEATED_KEY = [ ]

    @classmethod
    def repeatedKeys( cls ):
        return cls.REPEATED_KEY

    @classmethod
    def setRepeatedKeys( cls, a ):
        ProtobufDecoder.Debug.printmsg( ProtobufDecoder.Debug.METHOD_CALLING,  ( "repeated Key update :  %s -> %s" % ( cls.REPEATED_KEY, a ) ) )

        if isinstance( a, list):
            cls.REPEATED_KEY = a 
        else:
            cls.REPEATED_KEY = [ a ]

    @classmethod
    def clearRepeatedkeys( cls ):
        cls.setRepeatedKeys( [] )



    class PBLexer:
        #
        # Internal Mode Classes    
        #
        class Mode: ## Singleton
            def __new__(cls, *args, **kargs):
                if not hasattr(cls, "_instance"):
                    cls._instance = super(ProtobufDecoder.PBLexer.Mode, cls).__new__(cls)
                return cls._instance

            def __init__(self):
                self.buff = ""

                return

            def stringtoken( self ):
                s = self.buff
                self.buff = ""
                ProtobufDecoder.Debug.printmsg( ProtobufDecoder.Debug.LEXER_DETAIL,  ( "%s : string token '%s'" % (__class__ , s ) ) )
                return  { ProtobufDecoder.TOK_TYPE : ProtobufDecoder.TYPE_STRING, ProtobufDecoder.TOK_VALUE : s } 


            def nextchar( self, c ):
                return self, []

            def endchar( self ):
                ProtobufDecoder.Debug.printmsg( ProtobufDecoder.Debug.LEXER_DETAIL,  ( "%s : endchar 'EOF'" % __class__ ) )
                eof = { ProtobufDecoder.TOK_TYPE : ProtobufDecoder.TYPE_EOF_MARKER }
                if len( self.buff ) > 0 :
                    return self, [ self.stringtoken(), eof ]

                return self, [ eof ]


        ## Normal Loop
        class NormalMode(Mode):
            def nextchar( self, c ):
                ProtobufDecoder.Debug.printmsg( ProtobufDecoder.Debug.LEXER_DETAIL,  ( "%s : nextchar '%s'" % (__class__, c ) ) )
                a = []

                if c == '\'' :
                   return ProtobufDecoder.PBLexer.QuoteMode('\''), a

                if c == '"' :
                   return ProtobufDecoder.PBLexer.QuoteMode('"'), a


                elif c == ':' :
                   if( len( self.buff ) > 0 ):
                       a.append( self.stringtoken() )

                   a.append( { ProtobufDecoder.TOK_TYPE : ProtobufDecoder.TYPE_COLON })
                   ProtobufDecoder.Debug.printmsg( ProtobufDecoder.Debug.LEXER_TOKEN,  ( "%s : token" % __class__ ) , a )

                elif c == '<' or c == '{':
                   if( len( self.buff ) > 0 ):
                       a.append( self.stringtoken() )
    
                   a.append( { ProtobufDecoder.TOK_TYPE : ProtobufDecoder.TYPE_START })
                   ProtobufDecoder.Debug.printmsg( ProtobufDecoder.Debug.LEXER_TOKEN,  ( "%s : token" % __class__ ) , a )

                elif c == '>' or c == '}':
                   if( len( self.buff ) > 0 ):
                       a.append( self.stringtoken() )
    
                   a.append( { ProtobufDecoder.TOK_TYPE : ProtobufDecoder.TYPE_END })
                   ProtobufDecoder.Debug.printmsg( ProtobufDecoder.Debug.LEXER_TOKEN,  ( "%s : token" % __class__ ) , a )

                elif c == ' ' :
                   if( len( self.buff ) > 0 ):
                       a.append( self.stringtoken() )

                   ProtobufDecoder.Debug.printmsg( ProtobufDecoder.Debug.LEXER_TOKEN,  ( "%s : token" % __class__ ) , a )

                elif c == '\n' :
                   if( len( self.buff ) > 0 ):
                       a.append( self.stringtoken() )

                   ProtobufDecoder.Debug.printmsg( ProtobufDecoder.Debug.LEXER_TOKEN,  ( "%s : token" % __class__ ) , a )

                else:
                   self.buff += c           

                return self, a

        ## string only
        class QuoteMode(Mode):
            def __init__(self, q ):
                self.q = q
                self.inBackSlash = False
                super().__init__()


            def nextchar( self, c ):
                ProtobufDecoder.Debug.printmsg( ProtobufDecoder.Debug.LEXER_DETAIL,  ( "%s : nextchar '%s'" % (__class__, c ) ) )
                if( self.inBackSlash ):
                    self.inbackShash = False
                    self.buff +=c 

                elif c == '\\' :
                    self.inbackShash = True
            
                elif c == self.q :
                    return ProtobufDecoder.PBLexer.NormalMode(), [ self.stringtoken() ]

                self.buff +=c 

                return self, []

        ###
        ### PBLexer itself
        ###
        def __init__(self):
            self.mode = self.NormalMode()
            self.tlist = []


        def __iter__(self):
            return iter( self.tlist.copy() )

        def len( self ):
            ProtobufDecoder.Debug.printmsg( ProtobufDecoder.Debug.LEXER_INFO, ( "%s :  len %d" % ( __class__, len(self.tlist) ) ) )
            return len( self.tlist )

#        def getNextToken( self ):
#            ProtobufDecoder.Debug.printmsg( ProtobufDecoder.Debug.LEXER_INFO,  ( "%s :  get next token" % ( __class__, ) ) )
#            if( len( self.tlist ) > 0 ):
#                t = self.tlist[0]
#                del( self.tlist[0] )
#                return t

        def nextchar(self, c ):
            retmode, a = self.mode.nextchar( c )
##            ProtobufDecoder.Debug.printmsg( ProtobufDecoder.Debug.LEXER_INFO, ( "%s :  nextchar " %  __class__ ), a  )
    
            self.mode = retmode
            if len( a ) > 0 :
               self.tlist += a

        def endchar(self):
            ProtobufDecoder.Debug.printmsg( ProtobufDecoder.Debug.LEXER_INFO, ( "%s :  endchar " % ( __class__ ) ) )
            retmode, a = self.mode.endchar( )

#        def tokenList(self):
#            return self.tlist


        #
        # Internal Context Classes    
        #

    class Context:
        def __init__(self):
            return

        def parse( self, iterobj ):
            return [] ##dummy


    class InitContext(Context):
        def __init__(self ):
            super().__init__()
            self.curdict = {}
            self.result = []

        def parse( self, iterobj ):

            r = []
            while True:
                try:
                    t = next( iterobj )
                    ProtobufDecoder.Debug.printmsg( ProtobufDecoder.Debug.PARSER_DETAIL,  ( "%s :  token: " % ( __class__ ) ), [ t ] )

                    if( t[ ProtobufDecoder.TOK_TYPE ] == ProtobufDecoder.TYPE_STRING ):
                        self.setResult( ProtobufDecoder.ColonContext( t[ ProtobufDecoder.TOK_VALUE ] ).parse( iterobj ) )
         
                    elif( t[ ProtobufDecoder.TOK_TYPE ] == ProtobufDecoder.TYPE_START ):
                        self.setResult(  ProtobufDecoder.ArrayContext().parse( iterobj ) )

                    elif( t[ ProtobufDecoder.TOK_TYPE ] == ProtobufDecoder.TYPE_EOF_MARKER ):
                        ProtobufDecoder.Debug.printmsg( ProtobufDecoder.Debug.PARSER_DETAIL,  ( "%s :  EOF found" %  __class__ ) )
                        self.setResult(  ProtobufDecoder.ArrayContext().parse( iterobj ) )
                        break
                    else:
                        raise SyntaxErrorException("SyntaxError in %s" % t )

                except StopIteration:
                    break

            self.result.append( self.curdict )
            return self.result


        def setResult( self, r ):
            ProtobufDecoder.Debug.printmsg( ProtobufDecoder.Debug.PARSER_TOKEN,  ( "%s :  setResult %s " % ( __class__ , r ) ) )

            newdict_flag = False
            if r is None:
                ProtobufDecoder.Debug.printmsg( ProtobufDecoder.Debug.PARSER_TOKEN,  ( "%s :  r is nothing " % ( __class__ ) ) )
                return 

            for k in r:
                if( k in ProtobufDecoder.REPEATED_KEY ):
                    if( k in self.curdict ):
                        d = self.curdict[ k ]
                        if isinstance( d, list):
                            d.append( r[k] )
                        else:
                            na = [ d, r[k] ]
                            self.curdict[ k ] = na
                    else:
                        self.curdict[ k ] = r[k]
                    return

                if( k in self.curdict ):
                    self.result.append( self.curdict )
                    self.curdict = {}
                    self.curdict.update( r )
                    return
            
                self.curdict.update( r )

            return

    class ColonContext(Context):
        def __init__(self, keystring ):
            super().__init__()
            self.key = keystring

        def parse( self, iterobj ):

            try:

                t = next( iterobj )
                ProtobufDecoder.Debug.printmsg( ProtobufDecoder.Debug.PARSER_DETAIL,  ( "%s :  colon? " % ( __class__ ) ), [ t ] )

                if( t[ ProtobufDecoder.TOK_TYPE ] == ProtobufDecoder.TYPE_COLON ): ## ":" 
                    t2 = next( iterobj )
                    ProtobufDecoder.Debug.printmsg( ProtobufDecoder.Debug.PARSER_DETAIL,  ( "%s :  token2: " % ( __class__ ) ), [ t2 ] )

                    if( t2[ ProtobufDecoder.TOK_TYPE ] == ProtobufDecoder.TYPE_STRING ): ## key ":" "string"
                        ProtobufDecoder.Debug.printmsg( ProtobufDecoder.Debug.PARSER_DETAIL,  ( "%s :  colon return: %s:%s" % ( __class__, self.key, t2[ ProtobufDecoder.TOK_VALUE ] ) ) )
                        return  { self.key : t2[ ProtobufDecoder.TOK_VALUE ] }

                    elif( t2[ ProtobufDecoder.TOK_TYPE ] == ProtobufDecoder.TYPE_START ): ## key ":" "{"
                        r = ProtobufDecoder.ArrayContext().parse( iterobj )
                        ProtobufDecoder.Debug.printmsg( ProtobufDecoder.Debug.PARSER_DETAIL,  ( "%s :  colon return: %s:%s" % ( __class__, self.key , r ) )  )
                        return { self.key : r }

                    else:
                        raise SyntaxErrorException("SyntaxError in %s" % t )

                elif( t[ ProtobufDecoder.TOK_TYPE ] == ProtobufDecoder.TYPE_START ): ## ":" 
                    r = ProtobufDecoder.ArrayContext().parse( iterobj )
                    ProtobufDecoder.Debug.printmsg( ProtobufDecoder.Debug.PARSER_DETAIL,  ( "%s :  colon return: %s:%s" % ( __class__, self.key , r ) )  )
                    return { self.key : r }

                    ## ProtobufDecoder.Debug.printmsg( ProtobufDecoder.Debug.PARSER_DETAIL,  ( "%s :  no colon" % ( __class__ ) ) )
                    ## ProtobufDecoder.Debug.printmsg( ProtobufDecoder.Debug.PARSER_DETAIL,  ( "%s :  token1: " % ( __class__ ) ), [ t ] )

            except StopIteration:
               raise SyntaxErrorException("SyntaxError in %s" % t )

            return { "error!!": "colon error!!" }


    class ArrayContext(Context):
        def __init__(self):
            super().__init__()
            self.result = {}
        
        def parse( self, iterobj ):
            r = []
            while True:
                try:
                    t = next( iterobj )
                    ProtobufDecoder.Debug.printmsg( ProtobufDecoder.Debug.PARSER_DETAIL,  ( "%s :  token: " % ( __class__ ) ), [ t ] )

                    if( t[ ProtobufDecoder.TOK_TYPE ] == ProtobufDecoder.TYPE_STRING ): 
                        self.setResult( ProtobufDecoder.ColonContext( t[ ProtobufDecoder.TOK_VALUE ] ).parse( iterobj ) )

                    elif( t[ ProtobufDecoder.TOK_TYPE ] == ProtobufDecoder.TYPE_START ): ## "< <" Nested Array 
                        self.setResult( ProtobufDecoder.ArrayContext().parse( iterobj ) )
            
                    elif( t[ ProtobufDecoder.TOK_TYPE ] == ProtobufDecoder.TYPE_END ): ## ">" 
                        ProtobufDecoder.Debug.printmsg( ProtobufDecoder.Debug.PARSER_DETAIL,  ( "%s :  array Result: %s" % ( __class__ , self.result ) ) )
                        return self.result

                    else:
                        raise SyntaxErrorException("SyntaxError in %s" % t )

                except StopIteration:
                    break

            ProtobufDecoder.Debug.printmsg( ProtobufDecoder.Debug.PARSER_DETAIL,  ( "%s :  array Result2: %s" % ( __class__ , self.result ) ) )
            return self.result


        def setResult( self, r ):

            ProtobufDecoder.Debug.printmsg( ProtobufDecoder.Debug.PARSER_TOKEN,  ( "%s :  setResult %s " % ( __class__ , r ) ) )

            for k in r:
                if( k in self.result ):
                    d = self.result[ k ]
                    if isinstance( d, list):
                        d.append( r[k] )
                    else:
                        na = [ d, r[k] ]
                        self.result[ k ] = na
                else:
                    self.result[ k ] = r[k]

            ProtobufDecoder.Debug.printmsg( ProtobufDecoder.Debug.PARSER_TOKEN,  ( "%s :  Array holding :%s " % ( __class__ , self.result ) ) )

##
## ProtobufDecoder tself
##

    def __init__(self):
        self.fCxt = ProtobufDecoder.InitContext()


    def load( self, fp ):
        return self.dumps( fp.read() )

    def dump( self, fp ):
        return self.dumps( fp.read() )

    def dumps( self, d ):
        lexer = ProtobufDecoder.PBLexer()
        for c in d:
            lexer.nextchar( c )                   
        lexer.endchar()

        return ProtobufDecoder.InitContext().parse( iter( lexer ) )


def main():

    ProtobufDecoder.setRepeatedKeys( [ "params", "classification_list" ] )
    pb = ProtobufDecoder()

    if( len( sys.argv ) > 1 ):
        print( json.dumps( pb.dump( open( sys.argv[1], "r" ) ), indent=4 ) )

    else: ## stdin is file 
        print( json.dumps( pb.dump( sys.stdin ), indent=4 ) )


if __name__ == '__main__' :
    main()
