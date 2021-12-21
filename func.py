    def writemol2(self):
        coords = np.random.choice(self.Samples['coords'])
        # For reference of mol2 file format see the link https://chemicbook.com/2021/02/20/mol2-file-format-explained-for-beginners-part-2.html
        strings = []

        strings.append("# Name: combgel\n")
        strings.append("@<TRIPOS>MOLECULE\n")
        strings.append(self.name.replace('/','_')+"\n")
        strings.append(str(len(coords['id']))+' '+str(len(coords['bonds'])+7)+'\n')
        strings.append("SMALL\n")
        strings.append("USER_CHARGES\n")
        strings.append("@<TRIPOS>ATOM\n")
        
        coords_pos = coords['pos'] % self.box_l
        for i in range(len(coords['id'])):
            idx = coords['id'][i]
            name = self.NAMES[coords['type'][i]][0].upper()
            coord = coords_pos[i]
            #print("atom {} radius 1 name {} type {}\n".format(idx, typ, typ))
            #radius = 0.5
            #if typ in [self.TYPES['nodes'],self.TYPES['PA'],self.TYPES['PHA']]: radius = 1
            strings.append("{} {} {:3.3f} {:3.3f} {:3.3f} {}\n".format(idx, name, coord[0], coord[1], coord[2], name))
        strings.append("@<TRIPOS>BOND\n")
        
        i = 0
        for b in coords['bonds']:
            if len(b) > 0:
                for j in b[1:]:
                    if np.linalg.norm(coords_pos[b[0]] - coords_pos[j])<2.1:
                        strings.append("{} {} {} 1\n".format(i, b[0], j))
                        i+=1
            #print(i)
        strings[3] = str(len(coords['id']))+' '+str(i)+'\n'
        fp = open(self.fname+'.mol', mode='w+t')
        for s in strings:
            fp.write(s)
        fp.close()
        self.fnamemol = self.fname+'.mol'
        print ('structure saved in '+self.fnamemol)
        return
        
    def writevtf(self):


        fp = open(self.fname+'.vtf', mode='w+t')
        fp.write("unitcell {} {} {}\n".format(self.box_l,self.box_l,self.box_l))
        coords = np.random.choice(self.Samples['coords'])
        
        for i in range(len(coords['id'])):
            idx = coords['id'][i]
            typ = coords['type'][i]
            #print("atom {} radius 1 name {} type {}\n".format(idx, typ, typ))
            #radius = 0.5
            #if typ in [self.TYPES['nodes'],self.TYPES['PA'],self.TYPES['PHA']]: radius = 1
            radius = 1.0
            fp.write("atom {} radius {} name {} type {}\n".format(idx, radius, typ, typ))

        for b in coords['bonds']:
            if len(b) > 0:
                for i in b[1:]:
                    #print("bond {}:{}\n".format(b[0], i))
                    fp.write("bond {}:{}\n".format(b[0], i))

        fp.write("timestep indexed\n")
        for i in range(len(coords['id'])):
            pos = coords['pos'][i]  # % self.box_l is needed to wrap coordinates to simulation box
            idx = coords['id'][i]
            #print("{} {} {} {}\n".format(idx, pos[0], pos[1], pos[2]))
            fp.write("{} {} {} {}\n".format(idx, pos[0], pos[1], pos[2]))
        
        fp.close()
        self.fnamevtf = self.fname+'.vtf'
        #print (self.fnamevtf)
        return
        
        
    def VMD(self, run=False):
        self.writevtf()
        #input file
        vmd_title = open('vmd_title.tcl', "rt")
        types_text = 'set type_na {}\n'.format(self.TYPES['Na'])
        types_text += 'set type_cl {}\n'.format(self.TYPES['Cl'])
        types_text += 'set type_ca {}\n'.format(self.TYPES['Ca'])
        types_text += 'set type_pa {}\n'.format(self.TYPES['PA'])
        types_text += 'set type_pha {}\n'.format(self.TYPES['PHA'])
        types_text += 'set type_nodes {}\n\n'.format(self.TYPES['nodes'])
        
        
        vmd_title_txt = vmd_title.read()
        vmd_title.close()
        vmd_title_txt = types_text + vmd_title_txt.replace("Put a name of VFT file here", self.fnamevtf)
        vmd_title_txt += 'scale to 0.05\n'
        vmd_title_txt += 'render snapshot '+self.fname+'.tga\n'
        self.fnamevmd = self.fname+'.vmd'
        #output file to write the result to
        fout = open(self.fnamevmd, "wt")
        fout.write(vmd_title_txt)
        fout.close()
        print ('VMD vile saved: '+self.fnamevmd)
        if run:
            os.popen('vmd -e '+self.fnamevmd)
        else: 
            # this commands would render the vmd file            
            os.popen('echo exit >> '+self.fnamevmd)
            os.popen('vmd -dispdev text -e '+self.filename.vmd)
            os.popen('convert '+self.filename+'.tga '+self.filename+'.jpg')
            
        return        
        
                
