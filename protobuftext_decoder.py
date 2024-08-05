
import os,sys
import json


###
### protobuf text decoder
###
class ProtobufDecoder:

    TOK_TYPE="type"
    TOK_VALUE="value"
    TYPE_STRING = "string"
    TYPE_COLON = "COLON:"
    TYPE_START = "START<"
    TYPE_END   = ">END"

    class SyntaxErrorException( Exception ):
        pass

    REPEATED_KEY = [ ]

    @classmethod
    def repeatedKeys( cls ):
        return cls.REPEATED_KEY

    @classmethod
    def setRepeatedKeys( cls, a ):
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
                return  { ProtobufDecoder.TOK_TYPE : ProtobufDecoder.TYPE_STRING, ProtobufDecoder.TOK_VALUE : s } 


            def nextchar( self, c ):
                return self, []

            def endchar( self ):
                return self, [ self.stringtoken() ]

        ## Normal Loop
        class NormalMode(Mode):
            def nextchar( self, c ):
                a = []

                if c == '\'' :
                   return ProtobufDecoder.PBLexer.QuoteMode('\''), a

                if c == '"' :
                   return ProtobufDecoder.PBLexer.QuoteMode('"'), a


                elif c == ':' :
                   if( len( self.buff ) > 0 ):
                       a.append( self.stringtoken() )

                   a.append( { ProtobufDecoder.TOK_TYPE : ProtobufDecoder.TYPE_COLON })

                elif c == '<' :
                   if( len( self.buff ) > 0 ):
                       a.append( self.stringtoken() )
    
                   a.append( { ProtobufDecoder.TOK_TYPE : ProtobufDecoder.TYPE_START })

                elif c == '>' :
                   if( len( self.buff ) > 0 ):
                       a.append( self.stringtoken() )
    
                   a.append( { ProtobufDecoder.TOK_TYPE : ProtobufDecoder.TYPE_END })

                elif c == ' ' :
                   if( len( self.buff ) > 0 ):
                       a.append( self.stringtoken() )

                elif c == '\n' :
                       a.append( self.stringtoken() )

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


        def nextchar(self, c ):
            retmode, a = self.mode.nextchar( c )
    
            self.mode = retmode
            if len( a ) > 0 :
               self.tlist += a

        def endchar(self):
            retmode, a = self.mode.endchar( )

        def tokenList(self):
            return self.tlist


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

                    if( t[ ProtobufDecoder.TOK_TYPE ] == ProtobufDecoder.TYPE_STRING ):
                        self.setResult( ProtobufDecoder.ColonContext( t[ ProtobufDecoder.TOK_VALUE ] ).parse( iterobj ) )
         
                    elif( t[ ProtobufDecoder.TOK_TYPE ] == ProtobufDecoder.TYPE_START ):
                        self.setResult(  ProtobufDecoder.ArrayContext().parse( iterobj ) )
                    else:
                        raise SyntaxErrorException("SyntaxError in %s" % t )

                except StopIteration:
                    break

            self.result.append( self.curdict )
            return self.result


        def setResult( self, r ):
            ##self.result.append( r )
            ##print("%s setResult: %s" % ( self.__class__, r ) )

            newdict_flag = False
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

            ##print("%s setResult: Init Dict is %s " % ( self.__class__, self.result ) )


    class ColonContext(Context):
        def __init__(self, keystring ):
            super().__init__()
            self.key = keystring

        def parse( self, iterobj ):

            try:
                t = next( iterobj )

                if( t[ ProtobufDecoder.TOK_TYPE ] == ProtobufDecoder.TYPE_COLON ): ## ":" 
                    t2 = next( iterobj )

                    if( t2[ ProtobufDecoder.TOK_TYPE ] == ProtobufDecoder.TYPE_STRING ): ## ":" "string"
                        return  { self.key : t2[ ProtobufDecoder.TOK_VALUE ] }

                    elif( t2[ ProtobufDecoder.TOK_TYPE ] == ProtobufDecoder.TYPE_START ): ## ":" 
                        r = ProtobufDecoder.ArrayContext().parse( iterobj )
                        return { self.key : r }

                    else:
                        raise SyntaxErrorException("SyntaxError in %s" % t )

            except StopIteration:
               raise SyntaxErrorException("SyntaxError in %s" % t )



    class ArrayContext(Context):
        def __init__(self):
            super().__init__()
            self.result = {}
        
        def parse( self, iterobj ):
            r = []
            while True:
                try:
                    t = next( iterobj )
                    if( t[ ProtobufDecoder.TOK_TYPE ] == ProtobufDecoder.TYPE_STRING ): 
                        self.setResult( ProtobufDecoder.ColonContext( t[ ProtobufDecoder.TOK_VALUE ] ).parse( iterobj ) )

                    elif( t[ ProtobufDecoder.TOK_TYPE ] == ProtobufDecoder.TYPE_START ): ## "< <" Nested Array 
                        self.setResult( ProtobufDecoder.ArrayContext().parse( iterobj ) )
            
                    elif( t[ ProtobufDecoder.TOK_TYPE ] == ProtobufDecoder.TYPE_END ): ## ">" 
                        return self.result

                    else:
                        raise SyntaxErrorException("SyntaxError in %s" % t )

                except StopIteration:
                    break

            return self.curDict


        def setResult( self, r ):
            ##print("%s setResult: %s" % ( self.__class__, r ) )
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


            ##print("%s setResult: Array Dict is %s " % ( self.__class__, self.result ) )

##
## ProtobufDecoder tself
##

    def __init__(self):
        self.fCxt = ProtobufDecoder.InitContext()


    def dump( self, fp ):
        return self.dumps( fp.read() )


    def dumps( self, d ):
        lexer = ProtobufDecoder.PBLexer()
        for c in d:
            lexer.nextchar( c )                   
        lexer.endchar()

        return ProtobufDecoder.InitContext().parse( iter( lexer ) )


def main():

    ProtobufDecoder.setRepeatedKeys( [ "params" ] )
    pb = ProtobufDecoder()

    if( len( sys.argv ) > 1 ):
        print( json.dumps( pb.dump( open( sys.argv[1], "r" ) ), indent=4 ) )

    else: ## stdin is file 
        print( json.dumps( pb.dump( sys.stdin ), indent=4 ) )


if __name__ == '__main__' :
    main()
