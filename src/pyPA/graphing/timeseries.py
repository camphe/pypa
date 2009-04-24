__all__ = ['phy_plot']

HeadURL="$HeadURL$"
ChangeDate = "$LastChangedDate$"
RevisionNum= "$LastChangedRevision$"
ChangedBy  = "$LastChangedBy$"
__version__ = RevisionNum

from warnings import warn
from datetime import datetime
from pyPA.utils.util import AttrDict
from types import InstanceType
from pyPA.netcdf import NetCDFFile
from PseudoNetCDF.sci_var import PseudoNetCDFFile
from numpy import array, concatenate, zeros, arange
from pylab import figure, title, plot_date, savefig, legend, axis, grid, axes, xlabel, ylabel, subplot
from matplotlib.dates import DateFormatter, date2num
from matplotlib.cm import get_cmap
from matplotlib.font_manager import FontProperties
import re
import operator
import os

def add_mech(conf):
    if conf.has_key('mech'):
        mech = conf.mech
    else:
	from net_balance import get_pure_mech
        mech = conf.mech = get_pure_mech('_'.join([conf.mechanism.lower(),conf.model.lower()]))
        if isinstance(conf.mrgfile, (PseudoNetCDFFile, InstanceType)):
            mrg_file = conf.mrgfile
        else:
            mrg_file = NetCDFFile(conf.mrgfile,'r')

        mech.set_mrg(mrg_file)

def get_date(mrg_file, conf):
    date_ints = mrg_file.variables['TFLAG'][:,0,:]
    date_objs = array([datetime.strptime("%iT%06i" % (d,t), "%Y%jT%H%M%S") for d,t in date_ints])
    if conf.end_date:
        date_objs = concatenate([date_objs[[0]]-(date_objs[-1]-date_objs[-2]), date_objs])
    else:
        date_objs = concatenate([date_objs, date_objs[[-1]]+(date_objs[-1]-date_objs[-2])])

    date_objs = date_objs.repeat(2,0)[1:-1]
    return date_objs

def rxn_plot(conf, mech, date_objs, species, species_options, nlines, combine, fig = None, cmap = None):
    species_obj = mech(species)
    reactions = mech.find_rxns(species_obj, species_obj, False)
    irr_plot(conf, mech, reactions, date_objs, species, species_options, nlines, combine, fig, cmap)

def prod_plot(conf, mech, date_objs, species, species_options, nlines, combine, fig = None, cmap = None):
    species_obj = mech(species)
    reactions = mech.find_rxns([], species_obj, True)
    irr_plot(conf, mech, reactions, date_objs, species, species_options, nlines, combine, fig, cmap)

def loss_plot(conf, mech, date_objs, species, species_options, nlines, combine, fig = None, cmap = None):
    species_obj = mech(species)
    reactions = mech.find_rxns(species_obj, [], True)
    irr_plot(conf, mech, reactions, date_objs, species, species_options, nlines, combine, fig, cmap)


def irr_plot(conf, mech, reactions, date_objs, species, species_options, nlines, combine, fig = None, cmap = None):
    units = mech.irr.units
    
    colors = iter(get_cmap(cmap)(arange(nlines, dtype = 'f')/(nlines-1)))
    if fig is None:
        fig = figure()
    ax = axes([0.1,0.4,.8,.5], **species_options)
    grid(True)
    title(conf.title % locals())
    species_obj = mech(species)
    reactions = [ rxn for rxn in reactions if rxn not in reduce(operator.add, combine) ]
    if combine != [()]:
        reactions = reactions + map(lambda t2: '+'.join(t2), combine)
    reactions = [ (abs(mech('(%s)[%s]' % (rxn, species))).sum(),rxn) for rxn in reactions]
    reactions.sort(reverse = True)
    reactions = [r for v,r in reactions]
    
    options = {}
    options.setdefault('linestyle', '-')
    options.setdefault('linewidth', 3)
    options.setdefault('marker', 'None')

    for rxn in reactions[:nlines-1]:
        options['color'] = colors.next()
        data = mech('(%s)[%s]' % (rxn, species))
        options['label'] = re.compile('\d+.\d+\*').sub('', str(mech(rxn).sum())).replace(' ', '')
        plot_date(date_objs, data.repeat(2,0), **options)

    data = zeros(data.shape, dtype = data.dtype)
    for rxn in reactions[nlines-1:]:
        data += mech('(%s)[%s]' % (rxn, species))
    options['label'] = 'other'
    plot_date(date_objs, data.repeat(2,0), **options)
    
    options['color'] = 'black'
    options['marker'] = 'o'
    options['label'] = 'Chem'
    try:
        data = mech('%s[%s]'  % (conf.chem, species)).array()
    except:
        warn('Using sum of reactions for %(species)s' % locals())
        data = mech.make_net_rxn(species_obj, species_obj, False)[species_obj]

    plot_date(date_objs, data.repeat(2,0), **options)

    xlabel('Time')
    ylabel(units)
    ax.xaxis.set_major_formatter(DateFormatter('%jT%H'))
    ax.set_xlim(date2num(date_objs[0]), date2num(date_objs[-1]))
    if species_options.has_key('ylim'):
        ax.set_ylim(*species_options['ylim'])

    fig.autofmt_xdate()
    
    legend(loc=(0,-0.8), prop = FontProperties(size=10))
    return fig

def rxn_plot(conf, mech, date_objs, species, species_options, nlines, combine, fig = None, cmap = None):
    species_obj = mech(species)
    reactions = mech.find_rxns(species_obj, species_obj, False)
    irr_plot(conf, mech, reactions, date_objs, species, species_options, nlines, combine, fig, cmap)

def prod_plot(conf, mech, date_objs, species, species_options, nlines, combine, fig = None, cmap = None):
    species_obj = mech(species)
    reactions = mech.find_rxns([], species_obj, True)
    irr_plot(conf, mech, reactions, date_objs, species, species_options, nlines, combine, fig, cmap)

def loss_plot(conf, mech, date_objs, species, species_options, nlines, combine, fig = None, cmap = None):
    species_obj = mech(species)
    reactions = mech.find_rxns(species_obj, [], True)
    irr_plot(conf, mech, reactions, date_objs, species, species_options, nlines, combine, fig, cmap)


def irr_plots(conf, nlines = 8, combine = [()], fmt = 'pdf', fig_name = "RXN", plot_func = rxn_plot):
    add_mech(conf)

    tz = {'camx': 'LST'}.get(conf.model.lower(),'UTC')
    
    date_objs = get_date(mech.mrg, conf)
    
    for species, species_options in conf.species.iteritems():
        fig = plot_func(conf, mech, date_objs, species, species_options, nlines = nlines, combine = combine)
        savefig(os.path.join(conf.outdir, '%s_%s.%s' % (species, fig_name, fmt)), format = fmt)

def rxn_plots(conf, nlines = 8, combine = [()], fmt = 'pdf'):
    irr_plots(conf, nlines, combine, fmt, fig_name = 'RXN', plot_func = rxn_plot)

def loss_plots(conf, nlines = 8, combine = [()], fmt = 'pdf'):
    irr_plots(conf, nlines, combine, fmt, fig_name = 'LOSS', plot_func = loss_plot)

def prod_plots(conf, nlines = 8, combine = [()], fmt = 'pdf'):
    irr_plots(conf, nlines, combine, fmt, fig_name = 'PROD', plot_func = prod_plot)


def chem_plot(conf, mech, date_objs, species, species_options, fig = None, cmap = None):
    units = mech.irr.units
    
    colors = iter(get_cmap(cmap)(arange(2, dtype = 'f')))
    if fig is None:
        fig = figure()
    ax = axes(**species_options)

    grid(True)
    title(conf.title % locals())
    species_obj = mech(species)
    producers = mech.make_net_rxn([], species_obj, True)
    consumers = mech.make_net_rxn(species_obj, [], True)
    
    options = {}
    options.setdefault('linestyle', '-')
    options.setdefault('linewidth', 3)
    options.setdefault('marker', 'None')

    options['color'] = colors.next()
    options['label'] = '$\mathit{P}$'
    plot_date(date_objs, producers[species_obj].repeat(2,0), **options)

    options['color'] = colors.next()
    options['label'] = '$\mathit{L}$'
    plot_date(date_objs, consumers[species_obj].repeat(2,0), **options)
    
    options['color'] = 'black'
    options['marker'] = 'o'
    options['label'] = 'Chem'
    try:
        data = mech('%s[%s]'  % (conf.chem, species)).array()
    except:
        warn('Using sum of reactions for %(species)s' % locals())
        data = (producers + consumers)[species_obj]

    plot_date(date_objs, data.repeat(2,0), **options)

    xlabel('Time')
    ylabel(units)
    ax.xaxis.set_major_formatter(DateFormatter('%jT%H'))
    ax.set_xlim(date2num(date_objs[0]), date2num(date_objs[-1]))
    if species_options.has_key('ylim'):
        ax.set_ylim(*species_options['ylim'])

    fig.autofmt_xdate()
    
    legend(prop = FontProperties(size=10))
    return fig

def chem_plots(conf, fmt = 'pdf'):
    add_mech(conf)
    
    tz = {'camx': 'LST'}.get(conf.model.lower(),'UTC')
        
    date_objs = get_date(mech.mrg, conf)
    
    for species, species_options in conf.species.iteritems():
        fig = chem_plot(conf, mech, date_objs, species, species_options)
        savefig(os.path.join(conf.outdir, '%s_CHEM.%s' % (species, fmt)), format = fmt)

def phy_plot(conf, mech, date_objs, species, species_options, fig = None, cmap = None):
    """
    conf - configuration obect that has title, 
           init, final, process, and species
           * title - string template that has access
                     to all local variables by name
           * mech - net_balance.Mechanism.Mechanism object
           * species - sp
    """
    units = mech.ipr.units
    nlines = len(conf.process)
    colors = iter(get_cmap(cmap)(arange(nlines, dtype = 'f')/(nlines-1)))

    if fig is None:
        fig = figure()
    
    ax = axes(**species_options)

    grid(True)
    title(conf.title % locals())
    options = {'color': 'k'}
    options.setdefault('linestyle', '-')
    options.setdefault('linewidth', 3)
    options.setdefault('marker', 'o')
    data = mech('%s[%s]'  % (conf.init, species)).array()
    plot_date(date_objs[::2], data, **options)
    options.setdefault('label', 'Conc')
    options['marker'] = 'x'
    data = mech('%s[%s]'  % (conf.final, species)).array()
    plot_date(date_objs[1::2], data, **options)
    
    for process in conf.process.keys():
        options = conf.process[process]
        options.setdefault('color', colors.next())
        options.setdefault('linestyle', '-')
        options.setdefault('linewidth', 3)
        options.setdefault('label', process)
        options.setdefault('marker', 'None')
        data = mech('(%s)[%s]' % (process, species)).array().repeat(2,0)
        if data.nonzero()[0].any() or not filter:
            plot_date(date_objs, data, **options)
            
    xlabel('Time')
    ylabel(units)
    ax.xaxis.set_major_formatter(DateFormatter('%jT%H'))
    ax.set_xlim(date2num(date_objs[0]), date2num(date_objs[-1]))
    if species_options.has_key('ylim'):
        ax.set_ylim(*species_options['ylim'])

    fig.autofmt_xdate()
    legend()
    return fig

def phy_plots(conf, filter = True, fmt = 'pdf'):
    add_mech(conf)
    
    units = mech.ipr.units

    date_objs = get_date(mech.mrg, conf)

    for species, species_options in conf.species.iteritems():
        try:
            fig = phy_plot(conf, mech,  date_objs, species, species_options)
            fig.savefig(os.path.join(conf.outdir, '%s_IPR.%s' % (species, fmt)), format = fmt)
        except KeyError, detail:
            warn(detail)
    
if __name__ == '__main__':
    conf = AttrDict()
    conf.mechanism = 'cb05'
    conf.model = 'camx'
    conf.mrgfile = '/Users/barronh/Development/net_balance/src/net_balance/testdata/test.mrg.nc'
    conf.species  = dict(HNO3={},
                        NO2={},
                        NO={},
                        NOx={},
                        NOyN={},
                        NTR={}
                        )
    conf.species = dict(NOyN={})
    conf.process = {'H_Trans': {}, 
                    'V_Trans': {},
                    'Emissions': {},
                    'Deposit': {},
                    'Aero_Chem': {},
                    'CHEM': {},
                    'Motion': {},
                    'TEMPADJ': {}
                    }
    conf.init = 'INIT'
    conf.final = 'FCONC'
    conf.chem = 'CHEM'
    conf.title = '%(species)s IPR plot'
    conf.outdir = '.'
    conf.end_date = True
    phy_plots(conf)
#    rxn_plot(conf, combine = [('RXN_01', 'RXN_02', 'RXN_03')])
    conf.title = '%(species)s IRR plot'
    rxn_plots(conf)
    conf.title = '%(species)s Chem plot'
    chem_plots(conf)