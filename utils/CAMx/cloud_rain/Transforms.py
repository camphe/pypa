__all__=['cloud_rain_center_time', 'cloud_rain_plus', 'cloud_rain_center_time_plus']
from numpy import array

from pyPA.utils.MetaNetCDF import add_derived, time_avg_new_unit
from pyPA.utils.sci_var import PseudoNetCDFFile, PseudoNetCDFVariables, PseudoNetCDFVariable
from pyPA.utils.CAMxFiles import cloud_rain as reg_cloud_rain

class cloud_rain_center_time(time_avg_new_unit):
    __reader__=reg_cloud_rain

class cloud_rain_plus(add_derived):
    __childclass__=reg_cloud_rain
    __addvars__=['PRECIP_RATE','FCLOUD']
    def __PRECIP_RATE__(self):
        if 'PRECIP' in self.variables.keys():
            val=self.variables['PRECIP']
        else:
            val=self.variables['RAIN']+self.variables['SNOW']+self.variables['GRAUPEL']
        var=PseudoNetCDFVariable(self,'PRECIP_RATE','f',('TSTEP','LAY','ROW','COL'),(val*10)**1.27)
        var.units='mm/h'
        var.long_name='PRECIP_RATE'.ljust(16)
        var.var_desc='PRECIP_RATE'.ljust(16)
        return var

    def __FCLOUD__(self):
        val=self.variables['CLOUD']>=5
        var=PseudoNetCDFVariable(self,'FCLOUD','i',('TSTEP','LAY','ROW','COL'),array(val,dtype='i'))
        var.units='None'
        var.long_name='FCLOUD'.ljust(16)
        var.var_desc='FCLOUD'.ljust(16)
        return var

class cloud_rain_center_time_plus(cloud_rain_plus):
    __childclass__=cloud_rain_center_time

