# -*- coding: utf-8 -*-
"""
Created on Tue Mar  6 15:36:52 2018

@author: Dell
"""

import numpy as np

import scipy.sparse as sp
from scipy.sparse import linalg as sl

class FEModel:
    def __init__(self):
        self.__nodes={}
        self.__beams={}
        self.__membrane3s={}
        self.__membrane4s={}
                
        self.__index=[]
        self.__dof=None
        #without restraint
        self.__K=None
        self.__M=None
        self.__C=None
        self.__f=None
        self.__d=None
        #with restraint
        self.__K_bar=None
        self.__M_bar=None
        self.__C_bar=None
        self.__f_bar=None
        self.__d_bar=None
        
        self.is_solved=False
        
    @property
    def node_count(self):
        return len(self.__nodes.items())

    @property
    def beam_count(self):
        return len(self.__beams.items())
    
    @property
    def quad_count(self):
        return len(self.__quads.items())

    @property
    def is_assembled(self):
        return self.__dof != None
        
    @property 
    def index(self):
        return self.__index

    @property
    def DOF(self):
        return self.__dof
    
    @property
    def K(self):
        if not self.is_assembled:
            Exception('The model has to be assembled first.')
        return self.__K
    @property
    def M(self):
        if not self.is_assembled:
            Exception('The model has to be assembled first.')
        return self.__M    
    @property
    def f(self):
        if not self.is_assembled:
            Exception('The model has to be assembled first.')
        return self.__f
    @property
    def d(self):
        if not self.is_assembled:
            Exception('The model has to be assembled first.')
        return self.__d
    @property
    def K_(self):
        if not self.is_assembled:
            raise Exception('The model has to be assembled first.')
        return self.__K_bar
    @property
    def M_(self):
        if not self.is_assembled:
            Exception('The model has to be assembled first.')
        return self.__M_bar
    @property
    def f_(self):
        if not self.is_assembled:
            Exception('The model has to be assembled first.')
        return self.__f_bar
    @property
    def d_(self):
        if not self.is_assembled:
            Exception('The model has to be assembled first.')
        return self.__d_bar
        
    def add_node(self,node,tol=1e-6):
        """
        add node to model
        if node already exits, node will not be added.
        return: node hidden id
        """
#        res=self.find(list(self.__nodes.values()),node)
        res=[a.hid for a in self.__nodes.values() if abs(a.x-node.x)+abs(a.y-node.y)+abs(a.z-node.z)<1e-6]
        if res==[]:
            res=len(self.__nodes)
            node.hid=res
            self.__nodes[res]=node
        else:
            res=res[0]
        return res
        
    def add_beam(self,beam):
        """
        add beam to model
        if beam already exits, it will not be added.
        return: beam hidden id
        """
        res=[a.hid for a in self.__beams.values() 
            if (a.nodes[0]==beam.nodes[0] and a.nodes[1]==beam.nodes[1]) 
            or (a.nodes[0]==beam.nodes[1] and a.nodes[1]==beam.nodes[0])]
        if res==[]:
            res=len(self.__beams)
            beam.hid=res
            self.__beams[res]=beam
        else:
            res=res[0]
        return res
        
    def add_membrane3(self,elm):
        """
        add membrane to model
        if membrane already exits, it will not be added.
        return: membrane hidden id
        """
        res=len(self.__membrane3s)
        elm.hid=res
        self.__membrane3s[res]=elm
        return res
    
    def add_membrane4(self,elm):
        """
        add membrane to model
        if membrane already exits, it will not be added.
        return: membrane hidden id
        """
        res=len(self.__membrane4s)
        elm.hid=res
        self.__membrane4s[res]=elm
        return res
        
    def assemble_KM(self):
        """
        Assemble integrated stiffness matrix and mass matrix.
        """
        n_nodes=self.node_count
        self.__K = sp.lil_matrix((n_nodes*6, n_nodes*6))
        self.__M = sp.lil_matrix((n_nodes*6, n_nodes*6))     
        #Beam load and displacement, and reset the index 
        for beam in self.__beams.values():
            i = beam.nodes[0].hid
            j = beam.nodes[1].hid
            T=beam.transform_matrix
            Tt = T.transpose()

            #Static condensation to consider releases
            beam.static_condensation()
            Kij=beam.Ke_
            Mij=beam.Me_

            row=[a for a in range(0*6,0*6+6)]+[a for a in range(1*6,1*6+6)]
            col=[a for a in range(i*6,i*6+6)]+[a for a in range(j*6,j*6+6)]
            data=[1]*(2*6)
            G=sp.csr_matrix((data,(row,col)),shape=(2*6,n_nodes*6))
            
            Ke = sp.csr_matrix(np.dot(np.dot(Tt,Kij),T))
            Me = sp.csr_matrix(np.dot(np.dot(Tt,Mij),T))
            self.__K+=G.transpose()*Ke*G #sparse matrix use * as dot.
            self.__M+=G.transpose()*Me*G #sparse matrix use * as dot.
        
        for elm in self.__membrane3s.values():
            i = elm.nodes[0].hid
            j = elm.nodes[1].hid
            k = elm.nodes[2].hid
            
            T=elm.transform_matrix
            Tt = T.transpose()

            Ke=elm.Ke
            Me=elm.Me

            row=[a for a in range(0*6,0*6+6)]+[a for a in range(1*6,1*6+6)]+[a for a in range(2*6,2*6+6)]
            col=[a for a in range(i*6,i*6+6)]+[a for a in range(j*6,j*6+6)]+[a for a in range(k*6,k*6+6)]
            elm_node_count=3
            data=[1]*(elm_node_count*6)
            G=sp.csr_matrix((data,(row,col)),shape=(elm_node_count*6,n_nodes*6))
            
            Ke = sp.csr_matrix(np.dot(np.dot(Tt,Ke),T))
            Me = sp.csr_matrix(np.dot(np.dot(Tt,Me),T))
            self.__K+=G.transpose()*Ke*G #sparse matrix use * as dot.
            self.__M+=G.transpose()*Me*G #sparse matrix use * as dot.
            
        for elm in self.__membrane4s.values():
            i = elm.nodes[0].hid
            j = elm.nodes[1].hid
            k = elm.nodes[2].hid
            l = elm.nodes[3].hid
            
            T=elm.transform_matrix
            Tt = T.transpose()

            Ke=elm.Ke
            Me=elm.Me
            
            row=[]
            col=[]
            for i in range(4):
                row+=[a for a in range(i*6,i*6+6)]
            for _i in [i,j,k,l]:
                col+=[a for a in range(_i*6,_i*6+6)]
            elm_node_count=4
            data=[1]*(elm_node_count*6)
            G=sp.csr_matrix((data,(row,col)),shape=(elm_node_count*6,n_nodes*6))
            
            Ke = sp.csr_matrix(np.dot(np.dot(Tt,Ke),T))
            Me = sp.csr_matrix(np.dot(np.dot(Tt,Me),T))
            self.__K+=G.transpose()*Ke*G #sparse matrix use * as dot.
            self.__M+=G.transpose()*Me*G #sparse matrix use * as dot.
        #### other elements

    def assemble_f(self):
        """
        Assemble load vector and displacement vector.
        """
        n_nodes=self.node_count
        self.__f = sp.lil_matrix((n_nodes*6,1))
        #Beam load and displacement, and reset the index
        for node in self.__nodes.values():
            T=node.transform_matrix.transpose()
            self.__f[node.hid*6:node.hid*6+6,0]=np.dot(T,node.fn)        
            
        for beam in self.__beams.values():
            i = beam.nodes[0].hid
            j = beam.nodes[1].hid 
            #Transform matrix
            Vl=np.matrix(beam.local_csys.transform_matrix)
            V=np.zeros((12, 12))
            V[:3,:3] =V[3:6,3:6]=V[6:9,6:9]=V[9:,9:]=Vl
            Vt = V.transpose()
            
            row=[a for a in range(0*6,0*6+6)]+[a for a in range(1*6,1*6+6)]
            col=[a for a in range(i*6,i*6+6)]+[a for a in range(j*6,j*6+6)]
            data=[1]*(2*6)
            G=sp.csr_matrix((data,(row,col)),shape=(2*6,n_nodes*6))
            #Assemble nodal force vector
            self.__f += G.transpose()*np.dot(Vt,beam.re)
        #### other elements

    def assemble_boundary(self):
#        Logger.info('Eliminating matrix...')
        self.__K_bar=self.K.copy()
        self.__M_bar=self.M.copy()
        self.__f_bar=self.f.copy()
        self.__dof=self.node_count*6
        for node in self.__nodes.values():
            i=node.hid
            for j in range(6):
                if node.dn[j]!= None:
                    self.__K_bar[i*6+j,i*6+j]*=1e10
                    self.__M_bar[i*6+j,i*6+j]*=1e10
                    self.__f_bar[i*6+j]=self.__K_bar[i*6+j,i*6+j]*node.dn[j]
                    self.__dof-=1
        
    def find(self,nodes,target,tol=1e-6):
        """
        binary search target in nodes.
        nodes；node list to search
        target: node to find
        [tol]: tolerance
        return: node id or False
        """
        if len(nodes)==0:
            return False
        if len(nodes)==1:
            dist=abs(nodes[0].x-target.x)+abs(nodes[0].y-target.y)+abs(nodes[0].z-target.z)
            if dist<tol:
                return nodes[0].hid
            else:
                return False
        mid=len(nodes)//2
        A=nodes[:mid]
        B=nodes[mid:]
        return self.find(A,target) or self.find(B,target)

def solve_linear(model):
    K_,f_=model.K_,model.f_
    #sparse matrix solution
#    u,s,vt=sl.svds(sp.csr_matrix(K_),k=model.K_.shape[0]-1)
#    print(s)
#    pinv=np.dot(np.dot(vt.T,np.linalg.pinv(np.diag(s))),u.T)
##    pinv=np.linalg.pinv(K_.toarray())
#    delta =np.dot(pinv,f_.toarray())
    delta,info=sl.gmres(K_,f_.toarray())
    model.is_solved=True
    return delta.reshape((model.node_count*6,1))
    
if __name__=='__main__':
    np.set_printoptions(precision=1,suppress=True)
    
#FEModel Test
