'''
Created on 15 avr. 2020

@author: laurentmichel
'''
from lxml import etree
from product_annoter.mapper import logger
from copy import deepcopy
from product_annoter.mapper.constants import ATTRIBUTE_DEFAULT
class ParameterAppender:
    '''
    classdocs
    '''
    
    def __init__(self, param_template, mango_path, component_path):
        '''
        Constructor
        '''
        self.param_template = param_template

        self.mango_path = mango_path
        logger.info("parse %s", self.mango_path)
        self.mango_tree = etree.parse(self.mango_path)
        
        self.component_path = component_path
        if self.component_path:
            logger.info("parse %s", self.component_path)
            self.param_tree = etree.parse(self.component_path)
        else:
            self.param_tree = None

        
        self.mango_clean_tree = None
    
    def _get_unique_element(self, elements):
        """
        raise an exception if the cardinality of elements is != 1
        This method is a macro used everywhere an XML element must be unique
        """
        if len(elements) == 1:
            return elements[0]
        raise Exception("elements must have one item not {}".format(len(elements)))
    
    #def _is_element_unique  (self, elements):
    #    """
    #    """
    #    return (len(elements) == 1)
     
    def _clean_tree(self):
        tree_string = etree.tostring(
            self.mango_tree)
                        
        parser = etree.XMLParser(remove_blank_text=True)
        self.mango_clean_tree = etree.fromstring (tree_string, parser)
        
    def _get_global_instance(self, globals_id):
        return self._get_unique_element(
            self.mango_tree.xpath("/MODEL_INSTANCE/GLOBALS/INSTANCE[@ID='" + globals_id + "']")
            )
        
        
    def add_globals_xx(self, xml_instance):
        """
        Add the instances serialized in  xml_instance the GLOBALS blocks
        The level 0 instances of  xml_instance having the samne ID as one of the child 
        instances of GLOBALS are ignored (logged)
        Deeper instances are not supposed to have an ID
                
        :param xml_instance: string representation of the block to be added to the GLOBALS
        :type xml_instance: string
        """
        globals_root = self.mango_tree.xpath("/MODEL_INSTANCE/GLOBALS")
        new_globals = etree.fromstring(xml_instance)
        for new_global in new_globals.xpath("/INSTANCE"):
            if "ID" in new_global.keys() :
                new_global_id = new_global.attrib["ID"]
                if len(self.mango_tree.xpath("/MODEL_INSTANCE/GLOBALS/INSTANCE[@ID='" + new_global_id + "']")) == 0:
                    logger.info("add instance with ID={} to globals".format(new_global_id))
                    self._get_unique_element(globals_root).append(new_global)
                else :
                    logger.info("instance with ID={} already exists globals".format(new_global_id))


         
    def add_globals(self):
        if not self.param_tree:
            return
        mango_globals = self.mango_tree.xpath('/MODEL_INSTANCE/GLOBALS') 
        param_globals = self.param_tree.xpath('/MODEL_INSTANCE/GLOBALS') 
        for global_ele in self._get_unique_element(param_globals).getchildren():
            logger.info("Adding globals ID=%s", global_ele.attrib["ID"])
            self._get_unique_element(mango_globals).append( global_ele )
            
    def add_param_parameter(self):
        if not self.param_tree:
            return
        parameters_block = self._get_unique_element(
            self.mango_tree.xpath("//COLLECTION[@dmrole='mango:MangoObject.parameters']")
            )
        param_block = self._get_unique_element(
            self.param_tree.xpath("//INSTANCE[@dmrole='root']")
            )
        
        logger.info("Adding parameter dmtype=%s", param_block.attrib["dmtype"])
        new_param = etree.fromstring(
            self.param_template
            )
        param_block = deepcopy(param_block)
        param_block.attrib["dmrole"] = "mango:Parameter.measure"
        new_param.append(param_block)
        parameters_block.append(new_param)

    def set_ref_or_value(self, host_role, value_role, value_or_ref):
        if value_or_ref.startswith("@") is True:
            self.set_ref(host_role, value_role, value_or_ref.replace("@", ""))
        else :
            self.set_value(host_role, value_role, value_or_ref)


    def set_ref(self, host_role, value_role, value_ref):
        """
        Set the @ref attribute of all ATTRIBUTEs having value_role as role and hosted by 
        an INSTANCE having host_role as role
        :param host_role: Role of the host INSTANCE of the ATTRIBUTE which @ref must be set
        :type host_role: String
        :param value_role: Role of the ATTRIBUTE which @ref must be set
        :type value_role: String
        :param value_ref: value to be set for the @ref of the selected attributes
        """
        blocks = self.mango_tree.xpath("//INSTANCE[@dmrole='" + host_role + "']")

        value_block = None
        found = False
        for block in blocks:
            if "ref" in block.attrib.keys():
                block = self._get_global_instance(block.attrib["ref"])

            subblocks = block.xpath(".//ATTRIBUTE[@dmrole='" + value_role + "']")
            for subblock in subblocks:
                if "ref" not in subblock.keys() or subblock.attrib["ref"].startswith("@@@"):
                    value_block = subblock
                    value_block.attrib["ref"] = value_ref
                    logger.info("Set ref of %s[%s] = %s",host_role, value_role, value_ref)
                    if "value" in value_block.attrib.keys():
                        logger.info("Remove @value from %s[%s]",host_role, value_role)
                        value_block.attrib.pop("value")
                        found = True
        if found is False:     
            logger.info("All %s>%s already set", host_role, value_role)
        
 
    def set_value(self, host_role, value_role, value_value):
        """
        Set the @value attributes of all ATTRIBUTEs having value_role as role and hosted by 
        an INSTANCE having host_role as role
        :param host_role: Role of the host INSTANCE of the ATTRIBUTE which @value must be set
        :type host_role: String
        :param value_role: Role of the ATTRIBUTE which @value must be set
        :type value_value: String
        :param value_value: value to be set for the @value of the selected attributes
        """
        blocks = self.mango_tree.xpath("//INSTANCE[@dmrole='" + host_role + "']")

        value_block = None
        found = False
        for block in blocks:
            if "dmref" in block.attrib.keys():
                block = self._get_global_instance(block.attrib["dmref"])

            subblocks = block.xpath(".//ATTRIBUTE[@dmrole='" + value_role + "']")
            for subblock in subblocks:
                if "value" not in subblock.keys() or subblock.attrib["value"].startswith("@@@"):
                    value_block = subblock
                    value_block.attrib["value"] = value_value
                    logger.info("Set value of %s[%s] = %s",host_role, value_role, value_value)
                    if "ref" in value_block.attrib.keys():
                        logger.info("Remove @ref from %s[%s]",host_role, value_role)
                        value_block.attrib.pop("ref")
                        found = True
                        
        if found is False:     
            logger.info("All %s>%s already set", host_role, value_role)

                    #return

    def set_dmref(self, host_role, dm_ref):
        """
        Set the dmref attribute with dm_ref for all INSTANCES having @dmrole=host_role and @dmref=@@@@@@
        
        :param host_role: role of the instance to be modified
        :type host_role: string
        :param dm_ref: dm reference 
        :type dm_ref: string
        """
        blocks = self.mango_tree.xpath("//INSTANCE[@dmrole='" + host_role + "']")
        found = False
        for block in blocks:
            if "dmref" in block.attrib.keys():
                if block.attrib["dmref"] == ATTRIBUTE_DEFAULT.TO_BE_SET:
                    logger.info("instance with @role={} to be set with dmref={} found".format(host_role, dm_ref))
                    block.attrib["dmref"] = dm_ref
                    found = True
        if found is False:
            logger.info("Cannot find instance with @role={} to set the dmref={}".format(host_role, dm_ref))
 
    def set_notset_value(self):
        """
        Set the @value attributes of ATTRIBUTE a @ref still to be set with ATTRIBUTE_DEFAULT.NOT_SET
        and remove the @ref attribute from the ATTRIBUTE element
        """
        notset_values = self.mango_tree.xpath("//ATTRIBUTE[@ref='" + ATTRIBUTE_DEFAULT.TO_BE_SET + "']")
        for notset_value  in notset_values:        
            logger.info("Set value of tag %s as NotSet", notset_value.attrib["dmrole"])
            notset_value.attrib["value"] = ATTRIBUTE_DEFAULT.NOT_SET
            if "ref" in notset_value.attrib.keys():        
                notset_value.attrib.pop("ref")    
                
    def set_param_semantic(self, ucd, semantic, description):
        logger.info("set ucd=%s and semantic=%s", ucd, semantic)
        self.set_value("mango:MangoObject.parameters", "mango:Parameter.ucd", ucd)
        self.set_value("mango:MangoObject.parameters", "mango:Parameter.semantic", semantic)
        self.set_value("mango:MangoObject.parameters", "mango:Parameter.description", description)
        
    def save(self, filepath):
        logger.info("save mapping bloc in %s", filepath)

        self._clean_tree()
        with open(filepath, 'wb') as output_file:
            etree.ElementTree(self.mango_clean_tree).write(
                output_file, 
                encoding="utf-8", 
                xml_declaration=False, 
                pretty_print=True)

    def tostring(self):
        self._clean_tree()
        return (etree.tostring(
            self.mango_clean_tree,
            pretty_print=True)).decode("utf-8")    
