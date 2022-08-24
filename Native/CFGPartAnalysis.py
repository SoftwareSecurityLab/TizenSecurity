#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""

Created on Thu Jun 11 00:17:30 2020
'''
    Note: Code customized
'''
@authors: Ali Kamali 
	  Sara Baradaran 
	  Mahdi Heidari

"""


import networkx as np
import angr,pyvex

class CFGPartAnalysis():
    project = None
    def __init__(self, project, cfg=None):
        self.project = project
        if cfg == None:
            self.cfg=project.analyses.CFGFast(data_references=True)
        else:
            self.cfg = cfg

    def getFuncAddress(self, funcName, plt=None ):
        """
            getting address of an function by it's name
        """
        found = [
            addr for addr,func in self.cfg.kb.functions.items()
            if funcName == func.name and (plt is None or func.is_plt == plt)
            ]
        if len( found ) > 0:
            #print("Found "+funcName+"'s address at "+hex(found[0])+"!")
            return found[0]
        else:
            raise Exception("No address found for function : "+funcName)

    def getFunctions(self):
        """
        get All functions of an project with it's address
        ex:(address,function object)
        """
        result=list()
        for addr,func in self.cfg.kb.functions.items():
            result.append((addr,func))
            
        return result
  
    def _getRBPTemps(self,vex):
        rbp_tmp=self.listOfWrTmpWithRegName(vex,'rbp')
        rbps=[]
        if len(rbp_tmp) > 0:
            rbp_tmp='t'+str(rbp_tmp[0].tmp)
            rbps.append(rbp_tmp)
            bio_cmd=[]
            for rbp_put in self._getListPutStmtByRegName(vex,'rbp'):
                if isinstance(rbp_put.data,pyvex.expr.RdTmp):
                    rbps.append(str(rbp_put.data))
        return rbps
        
    def resolveAddrByFunction(self,addr):
        """
        resolve the address with it's function .any address blong to the function
        """                
        for i in self.getFunctions():
            r=i[1]
            for block in r.blocks:
                try:
                    if addr in block.instruction_addrs:
                        return r
                except angr.errors.SimTranslationError:
                    pass
    
    def getCaller(self,func_name):
        """
        it search throw all functions and returns caller functions of this function
        """
        result=list()
        functions=self.getFunctions()
        for func in functions:
            call_sites=list(func[1].get_call_sites())
            for site in call_sites:
                block=self.project.factory.block(site)
                vex=block.vex
                if vex.jumpkind == 'Ijk_Call':
                    jump=self._getCallPROPSFromCFG(block.addr)
                    if jump:
                        jmp_node,jmp_type=jump
                        if jmp_node.is_simprocedure and 'Unresolvable' in jmp_node.name:
                            addr=self._tryToResolveJump(func[1].name,vex)
                            if addr:
                                if self.cfg.kb.functions[addr].name == func_name:
                                    result.append(func)
                        elif self.cfg.kb.functions[jmp_node.addr].name == func_name:
                            result.append(func)
                                                     
        return result
    
    def _getCallPROPSFromCFG(self,addr):
        target_node=self._getNodeInCFGGraph(addr)
        if target_node:
            jump=target_node.successors_and_jumpkinds()
            if len(jump) == 1:
                return jump[0]
    
    def _getNodeInCFGGraph(self,addr):
        for node in self.cfg.graph.nodes:
            if addr in node.instruction_addrs:
                return node
                
    def getAddressOfFunctionCall(self,func_name,dict_type=False):
        """
        returns address witch the target function is called 
        """
        if dict_type:
            result=dict()
        else:
            result=set()
        callers=self.getCaller(func_name)
        if len(callers)>0:
            for func in callers:
                addr=self.getFuncAddress(func_name)
                for i in func[1].blocks:
                    tmp_vex=i.vex
                    if tmp_vex.jumpkind == 'Ijk_Call':
                        jump=self._getCallPROPSFromCFG(i.addr)
                        if jump:
                            jmp_node,jmp_type=jump
                            res_addr=None
                            if jmp_node.is_simprocedure and 'Unresolvable' in jmp_node.name:
                                res_addr=self._tryToResolveJump(func[1].name,i.vex)
                            if (jmp_node.addr == addr) or res_addr:
                                if dict_type:
                                    key=func[1]
                                    value=tmp_vex.instruction_addresses[len(tmp_vex.instruction_addresses)-1]
                                    if key not in result.keys():
                                        result[key]=list()
                                    if value not in result[key]:
                                        result[key].append(value)
                                else:
                                    result.add((tmp_vex.instruction_addresses[len(tmp_vex.instruction_addresses)-1],func[1]))
        if dict_type:
            return result
        return list(result)
    
    def getRegsName(self,vex,offset):
        """
        given vex and offset of an register it returns register name for that offset
        """
        for  j in vex.arch.register_list: 
            if offset is j.vex_offset:
                 return j.name
           
    def getRegOffset(self,vex,reg_name):
        """
        return register offset of an register by it's name in an vex IRSB
        """
        for  j in vex.arch.register_list: 
            if j.name == reg_name:
                return j.vex_offset 

    def getVexListCommand(self,vex,vexType):
        """
        return list of Statement with type vexType
        """
        result=list()
        for i in vex.statements:
            if isinstance(i,vexType):
                result.append(i)

                    
        return result

    def listOfTempStmt(self,v,target):
        """
        list of statements withch target temp is part of it
        """
        import re
        result=list()
        for i in v.statements:
            tmp=i.__str__()
            if re.match(".*"+target+"\\D.*|.*"+target +"$",tmp) is None:
                continue
            result.append(i)
        return result

    def listOfWrTmpWithRegName(self,vex,reg_name):
        """
        returns list of Get Statement with offset of target register
        """
        tmp=self.getVexListCommand(vex,pyvex.IRStmt.WrTmp)
        getList=list()
        for i in tmp:
            if i.data.tag == 'Iex_Get':
                getList.append(i)
    
        result=list()
        for i in getList:
            offset=i.data.offset
            name=self.getRegsName(vex,offset)
            if reg_name == name:
                result.append(i)
                
        del(getList)
        return result
        
    def targetWrTempByTempName(self,vex,tmp_name):
        """
         returns WrStatement with it's taget is target temp
        """
        tmp=self.listOfTempStmt(vex,tmp_name)
        result=None
        for i in tmp:
            if isinstance(i,pyvex.IRStmt.WrTmp):
                if 't'+str(i.tmp) == tmp_name:
                    result=i
        
        return result
 
    def _getLastPutStmtByOffset(self,vex,offset):
        """
        return last put statement relative to target register offset
        """
        puts=self.getVexListCommand(vex,pyvex.IRStmt.Put)
        puts.reverse()
        for i in puts:
            if i.offset == offset:
                return i
        
        return None

    def getFunctionCalledBetweenBoundry(self,caller,start_addr,end_addr):
        '''
        return functions called between start address and end address in caller function
        '''
        caller=self.resolveAddrByFunction(self.getFuncAddress(caller)) 
        start_discover=False
        result=list()
        caller_blocks=list(caller.blocks)
        caller_blocks.sort(key=lambda b:b.addr)
        for i in caller_blocks:
            if ~start_discover:
                if start_addr in i.instruction_addrs:
                    start_discover=True
            if start_discover:
                if end_addr in i.instruction_addrs:
                    return result
                else:
                    if i.vex.jumpkind=='Ijk_Call':
                        jump=self._getCallPROPSFromCFG(i.addr)
                        if jump:
                            jmp_node,jmp_type=jump
                            if jmp_node.is_simprocedure and 'Unresolvable' in jmp_node.name:
                                addr=self._tryToResolveJump(caller.name,i.vex)
                                if addr:
                                    func=self.resolveAddrByFunction(addr)
                                    if func:
                                        result.append((addr,func.name))
                            else:
                                addr=jmp_node.addr
                                func=self.resolveAddrByFunction(addr)
                                if func:
                                    result.append((addr,func.name))
        return result
    
    def _tryToResolveJump(self,func_name,vex):
        stack={}
        for addr,value in self.getSimpleWrINStackFor(func_name):
            stack[addr]=value
        if len(stack) > 0:
            rbps=self._getRBPTemps(vex)
            if len(rbps) > 0:                        
                if isinstance(vex.next,pyvex.expr.RdTmp):
                    target_tmp=str(vex.next)
                    wr_target=self.targetWrTempByTempName(vex,target_tmp)
                    if isinstance(wr_target.data,pyvex.expr.Load) and isinstance(wr_target.data.addr,pyvex.expr.RdTmp):
                        addr_tmp=str(wr_target.data.addr)
                        addr_wr_target=self.targetWrTempByTempName(vex,addr_tmp)
                        if isinstance(addr_wr_target.data,pyvex.expr.Binop):
                            lhs,rhs=addr_wr_target.data.args
                            if isinstance(lhs,pyvex.expr.RdTmp) and isinstance(rhs,pyvex.expr.Const):
                                if str(lhs) in rbps:
                                    if rhs.con.value in stack.keys():
                                        addr=stack[rhs.con.value]
                                        if self.isFunctionAddr(addr):
                                            return addr
        
    def getSimpleWrINStackFor(self,func_name,with_addr=False,block=None):
        func=self.resolveAddrByFunction(self.getFuncAddress(func_name))
        blocks=[]
        if block:
            blocks.append(block)
        else:
            blocks=func.blocks
        result=[]
        for blck in blocks:
            value=[]
            addrs=[]
            items=self._getWritesInStack(blck.vex)
            while len(items) > 0:
                item=items.pop()
                if item[0] not in addrs:
                    value.append((blck.addr,item))
                    addrs.append(item[0])
            result.extend(value)
        b_list={}
        tmp_res={}
        for addr ,props in result:
            key=props[0]
            if key not in b_list.keys() or b_list[key] <addr:
                b_list[key]=addr
                if with_addr:
                    tmp_res[key]=(addr,props) 
                else:
                    tmp_res[key]=props

        return list(tmp_res.values())
    
    def _getWritesInStack(self,vex):
        rbp_tmp=self.listOfWrTmpWithRegName(vex,'rbp')
        result=[]
        rbps=self._getRBPTemps(vex)
        for i in self.getVexListCommand(vex,pyvex.IRStmt.Store):
            if isinstance(i.data,pyvex.expr.Const) and isinstance(i.addr,pyvex.expr.RdTmp):
                src_tmp=str(i.addr)
                wr_target=self.targetWrTempByTempName(vex,src_tmp)
                if isinstance(wr_target,pyvex.stmt.WrTmp) and isinstance(wr_target.data,pyvex.expr.Binop):
                    lhs=wr_target.data.args[0]
                    rhs=wr_target.data.args[1]
                    if isinstance(lhs,pyvex.expr.RdTmp):
                        rbp_put=self._getLastPutStmtByOffset(vex,self.getRegOffset(vex,'rbp'))
                        if rbp_put is not None:
                            if self.getAddressStatement(vex,rbp_put) < self.getAddressStatement(vex,wr_target):
                                if isinstance(rbp_put.data,pyvex.expr.RdTmp):
                                    tmp_put=str(rbp_put.data)
                                    if (str(lhs) == tmp_put) or (str(lhs) in rbps):
                                        val=i.data.con.value
                                        if val in range(self.project.loader.min_addr,self.project.loader.max_addr):
                                            if self.isFunctionAddr(val)==False:
                                                str_len=self._est_str_length(val)
                                                val=self.project.loader.memory.load(val,str_len)
                                        result.append( (rhs.con.value,val))
                        elif str(lhs) in rbps:
                            val=i.data.con.value
                            if val in range(self.project.loader.min_addr,self.project.loader.max_addr):
                                if self.isFunctionAddr(val)==False:
                                    str_len=self._est_str_length(val)
                                    val=self.project.loader.memory.load(val,str_len)
                                ##
                            result.append( (rhs.con.value,val))
        return result