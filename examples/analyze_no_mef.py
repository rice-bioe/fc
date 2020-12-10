#!/usr/bin/python
"""
FlowCal Python API example, without using calibration beads data.

This script is divided in two parts. Part one processes data from ten cell
samples and generates plots of each one.

Part two exemplifies how to use the processed cell sample data with
FlowCal's plotting and statistics modules to produce interesting plots.

For details about the experiment, samples, and instrument used, please
consult readme.txt.

"""
import os
import os.path
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
import FlowCal

###
# Definition of constants
###

# Names of the FCS files containing data from cell samples
samples_filenames = ['FCFiles/sample029.fcs',
                     'FCFiles/sample030.fcs',
                     'FCFiles/sample031.fcs',
                     'FCFiles/sample032.fcs',
                     'FCFiles/sample033.fcs',
                     'FCFiles/sample034.fcs',
                     'FCFiles/sample035.fcs',
                     'FCFiles/sample036.fcs',
                     'FCFiles/sample037.fcs']

# aTc concentration of each cell sample, in ng/mL.
atc = np.array([0, 0.5, 1, 1.5, 2, 3, 4, 7.5, 20])

# Plots will be generated after gating and transforming cell samples. These
# will be stored in the following folder.
samples_plot_dir = 'plot_samples'

if __name__ == "__main__":

    # Check that plot directory exists, create if it does not.
    if not os.path.exists(samples_plot_dir):
        os.makedirs(samples_plot_dir)

    ###
    # Part 1: Processing cell sample data
    ###
    print("\nProcessing cell samples...")

    # We will use the list ``samples`` to store processed, transformed flow
    # cytometry data of each sample.
    samples = []

    # Iterate over cell sample filenames
    for sample_id, sample_filename in enumerate(samples_filenames):

        # Load flow cytometry data from the corresponding FCS file.
        # ``FlowCal.io.FCSData(filename)`` returns an object that represents
        # flow cytometry data loaded from file ``filename``.
        print("\nLoading file \"{}\"...".format(sample_filename))
        sample = FlowCal.io.FCSData(sample_filename)
        
        # Data loaded from an FCS file is in "Channel Units", the raw numbers
        # reported from the instrument's detectors. The FCS file also contains
        # information to convert these into Relative Fluorescence Intensity
        # (RFI) values, commonly referred to as arbitrary fluorescence units
        # (a.u.). The function ``FlowCal.transform.to_rfi()`` performs this
        # conversion.
        print("Performing data transformation...")
        sample = FlowCal.transform.to_rfi(sample)

        # Gating

        # Gating is the process of removing measurements of irrelevant
        # particles while retaining only the population of interest.
        print("Performing gating...")

        # ``FlowCal.gate.start_end()`` removes the first and last few events.
        # Transients in fluidics can make these events slightly different from
        # the rest. This may not be necessary in all instruments.
        sample_gated = FlowCal.gate.start_end(sample,
                                              num_start=250,
                                              num_end=100)

        # ``FlowCal.gate.high_low()`` removes events outside a range specified
        # by a ``low`` and a ``high`` value. If these are not specified (as
        # shown below), the function removes events outside the channel's range
        # of detection.
        # Detectors in a flow cytometer have a finite range of detection. If the
        # fluorescence of a particle is higher than the upper limit of this
        # range, the instrument will incorrectly record it with a value equal to
        # this limit. The same happens for fluorescence values lower than the
        # lower limit of detection. These saturated events should be removed,
        # otherwise statistics may be calculated incorrectly.
        # Note that this might not be necessary with newer instruments that
        # record data as floating-point numbers (and in fact it might eliminate
        # negative events). To see the data type stored in your FCS files, run
        # the following instruction: ``print sample_gated.data_type``.
        # We will remove saturated events in the forward/side scatter channels,
        # and in the fluorescence channel FL1.
        sample_gated = FlowCal.gate.high_low(sample_gated,
                                             channels=['FSC','SSC','FL1','FL2'])

        # ``FlowCal.gate.density2d()`` preserves only the densest population as
        # seen in a 2D density diagram of two channels. This helps remove
        # particle aggregations and other sparse populations that are not of
        # interest (i.e. debris).
        # We use the forward and side scatter channels and preserve 85% of the
        # events. Finally, setting ``full_output=True`` instructs the function
        # to return additional outputs in the form of a named tuple.
        # ``gate_contour`` is a curve surrounding the gated region, which we
        # will use for plotting later.
        density_gate_output = FlowCal.gate.density2d(
            data=sample_gated,
            channels=['FSC','SSC'],
            gate_fraction=0.85,
            full_output=True)
        sample_gated = density_gate_output.gated_data
        gate_contour = density_gate_output.contour

        # Plot forward/side scatter 2D density plot and 1D fluorescence
        # histograms
        print("Plotting density plot and histogram...")

        # Parameters for the forward/side scatter density plot
        density_params = {}
        # We use the "scatter" mode, in which individual particles will be
        # plotted individually as in a scatter plot, but with a color
        # proportional to the particle density around.
        density_params['mode'] = 'scatter'

        # Parameters for the fluorescence histograms
        hist_params = [{}, {}]
        hist_params[0]['xlabel'] = 'FL1 Fluorescence (a.u.)'
        hist_params[1]['xlabel'] = 'FL2 Fluorescence (a.u.)'

        # Plot filename
        # The figure can be saved in any format supported by matplotlib (svg,
        # jpg, etc.) by just changing the extension.
        plot_filename = '{}/density_hist_{}.png'.format(
            samples_plot_dir,
            'S{:03}'.format(sample_id + 1))

        # Plot and save
        # The function ``FlowCal.plot.density_and_hist()`` plots a combined
        # figure with a 2D density plot at the top and an arbitrary number of
        # 1D histograms below. In this case, we will plot the forward/side
        # scatter channels in the density plot and a histogram of the
        # fluorescence channel FL1 below.
        # Note that we are providing data both before (``sample``) and after
        # (``sample_gated``) gating. The 1D histogram will display the ungated
        # dataset with transparency and the gated dataset in front with a solid
        # color. In addition, we are providing ``gate_contour`` from the
        # density gating step, which will be displayed in the density diagram.
        # This will result in a convenient representation of the data both
        # before and after gating.
        FlowCal.plot.density_and_hist(
            sample,
            sample_gated,
            density_channels=['FSC','SSC'],
            hist_channels=['FL1','FL2'],
            gate_contour=gate_contour,
            density_params=density_params,
            hist_params=hist_params,
            savefig=plot_filename)

        # Save cell sample object
        samples.append(sample_gated)

    ###
    # Part 3: Examples on how to use processed cell sample data
    ###

    # Plot 1: Histogram of all samples
    #
    # Here, we plot the fluorescence histograms of all ten samples in the same
    # figure using ``FlowCal.plot.hist1d``. Note how this function can be used
    # in the context of accessory matplotlib functions to modify the axes
    # limits and labels and to add a legend, among other things.

    # Color each histogram according to its corresponding aTc concentration.
    # Use a perceptually uniform colormap (cividis), and transition among
    # colors using a logarithmic normalization, which comports with the
    # logarithmically spaced aTc concentrations.
    cmap = mpl.cm.get_cmap('cividis')
    norm = mpl.colors.LogNorm(vmin=1e0, vmax=20)
    colors = [cmap(norm(atc_i)) if atc_i > 0 else cmap(0.0)
              for atc_i in atc]

    plt.figure(figsize=(6, 5.5))
    plt.subplot(2, 1, 1)
    FlowCal.plot.hist1d(samples,
                        channel='FL1',
                        histtype='step',
                        bins=128,
                        edgecolor=colors)
    plt.ylim((0,2500))
    plt.xlim((0,5e3))
    plt.xlabel('FL1 Fluorescence (a.u.)')
    plt.legend(['{:.1f} ng/mL aTc'.format(i) for i in atc],
               loc='upper left',
               fontsize='small')

    plt.subplot(2, 1, 2)
    FlowCal.plot.hist1d(samples,
                        channel='FL2',
                        histtype='step',
                        bins=128,
                        edgecolor=colors)
    plt.ylim((0,2500))
    plt.xlim((0,5e3))
    plt.xlabel('FL2 Fluorescence (a.u.)')
    plt.legend(['{:.1f} ng/mL aTc'.format(i) for i in atc],
               loc='upper left',
               fontsize='small')

    plt.tight_layout()
    plt.savefig('histograms.png', dpi=200)
    plt.close()

    # Plot 2: Dose response curve
    #
    # Here, we illustrate how to obtain statistics from the fluorescence of
    # each sample and how to use them in a plot. The stats module contains
    # functions to calculate different statistics such as mean, median, and
    # standard deviation. In this example, we calculate the mean from channel
    # FL1 of each sample and plot them against the corresponding aTc
    # concentrations.

    # Because some of our control samples were measured at a different cytometer
    # gain setting and we aren't using MEF calibration here, we will use the 0
    # and 20 ng/mL aTc concentration samples instead.
    samples_fl1 = [FlowCal.stats.mean(s, channels='FL1') for s in samples]
    samples_fl2 = [FlowCal.stats.mean(s, channels='FL2') for s in samples]

    plt.figure(figsize=(6,3))

    plt.subplot(1, 2, 1)
    plt.plot(atc,
             samples_fl1,
             marker='o',
             color='tab:green')
    plt.axhline(samples_fl1[0],
                color='gray',
                linestyle='--',
                zorder=-1)
    plt.text(s='Min', x=3e1, y=1.5e1, ha='left', va='bottom', color='gray')
    plt.axhline(samples_fl1[-1],
                color='gray',
                linestyle='--',
                zorder=-1)
    plt.text(s='Max', x=-0.8, y=2.5e2, ha='left', va='top', color='gray')
    plt.yscale('log')
    plt.ylim((5e0,5e2))
    plt.xscale('symlog')
    plt.xlim((-1e0, 1e2))
    plt.xlabel('aTc Concentration (ng/mL)')
    plt.ylabel('FL1 Fluorescence (a.u.)')

    plt.subplot(1, 2, 2)
    plt.plot(atc,
             samples_fl2,
             marker='o',
             color='tab:orange')
    plt.axhline(samples_fl2[0],
                color='gray',
                linestyle='--',
                zorder=-1)
    plt.text(s='Min', x=3e1, y=1.35e1, ha='left', va='bottom', color='gray')
    plt.axhline(samples_fl2[-1],
                color='gray',
                linestyle='--',
                zorder=-1)
    plt.text(s='Max', x=-0.8, y=6e2, ha='left', va='top', color='gray')
    plt.yscale('log')
    plt.ylim((4e0,1.5e3))
    plt.xscale('symlog')
    plt.xlim((-1e0, 1e2))
    plt.xlabel('aTc Concentration (ng/mL)')
    plt.ylabel('FL2 Fluorescence (a.u.)')

    plt.tight_layout()
    plt.savefig('dose_response.png', dpi=200)
    plt.close()

    # Plot 3: Dose response violin plot
    #
    # Here, we use a violin plot to show the fluorescence of (almost) all
    # cells as a function of aTc. (The `upper_trim_fraction` and
    # `lower_trim_fraction` parameters eliminate the top and bottom 1% of
    # cells from each violin for aesthetic reasons. The summary statistic,
    # which is illustrated as a horizontal line atop each violin, is
    # calculated before cells are removed, though.) We again use the 0 and 20
    # ng/mL aTc concentration samples as the min and max data in lieu of
    # controls. We also set `yscale` to 'log' because the cytometer used to
    # collect this data produces positive integer data (as opposed to
    # floating-point data, which can sometimes be negative), so the added
    # complexity of a logicle y-scale (which is the default) is not necessary.
    plt.figure(figsize=(8,3.5))
    
    plt.subplot(1, 2, 1)
    FlowCal.plot.violin_dose_response(
        data=samples,
        channel='FL1',
        positions=atc,
        min_data=samples[0],
        max_data=samples[-1],
        violin_kwargs={'facecolor':'tab:green',
                       'edgecolor':'black'},
        violin_width_to_span_fraction=0.075,
        xscale='log',
        yscale='log',
        ylim=(1e0,1e3))
    plt.xlabel('aTc Concentration (ng/mL)')
    plt.ylabel('FL1 Fluorescence (a.u.)')
    
    plt.subplot(1, 2, 2)
    FlowCal.plot.violin_dose_response(
        data=samples,
        channel='FL2',
        positions=atc,
        min_data=samples[0],
        max_data=samples[-1],
        violin_kwargs={'facecolor':'tab:orange',
                       'edgecolor':'black'},
        violin_width_to_span_fraction=0.075,
        xscale='log',
        yscale='log',
        ylim=(1e0,2e3))
    plt.xlabel('aTc Concentration (ng/mL)')
    plt.ylabel('FL2 Fluorescence (a.u.)')

    plt.tight_layout()
    plt.savefig('dose_response_violin.png', dpi=200)
    plt.close()

    print("\nDone.")
