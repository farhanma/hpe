#!/usr/bin/perl -w

use strict;
use Getopt::Long qw(:config no_ignore_case);
use Pod::Usage;
use POSIX;


my $defaultNB = 168;

sub usage()
{
    print STDERR "Usage: hpl_rungen.pl (-n nprocs|--nprocs=nprocs)\n" .
                 "                     (-m mem|--mem=mem)\n" .	
                 "                     [-N ppn|--ppn=ppn]\n" .
                 "                     [-S pps|--pps=pps]\n" .
                 "                     [-j cpus]\n" .
                 "                     [-b nb|--nb=nb]\n" .
                 "                     [-d threads|--depth=threads]\n" .
                 "                     [--[no]optdist]\n" .
                 "                     [-v|--verbose]\n" .
                 "                     [-q|--quiet]\n";
    print STDERR "  nprocs  = number of MPI processes (aka core count)\n";
    print STDERR "  mem     = memory usage per process in MB\n";
    print STDERR "            or GB with \"G\" suffix\n";
    print STDERR "  ppn     = processors per node (cores per node)\n";
    print STDERR "            default is 16\n";
    print STDERR "  pps     = processors per node (PEs per numanode)\n";
    print STDERR "            default is undefined\n";
    print STDERR "  cpus    = CPUs to use per compute unit (2 for Intel Hyper-Threading)\n";
    print STDERR "            default is 1\n";
    print STDERR "  nb      = blocksize\n";
    print STDERR "            default is $defaultNB\n";
    print STDERR "  threads = number of threads\n";
    print STDERR "  --[no]optdist : [don't try to] size problem to distribute evenly over procs\n";
    print STDERR "  -v|--verbose  : default amount of informative messages\n";
    print STDERR "  -q|--quiet    : no informative messages\n";
    print STDERR "  --dryrun      : don't write any files\n";
    exit;
}

&usage() unless (@ARGV > 2);

my ($ncpus, $nnodes, $mem, $ppn, $cpuspercu, $pps, $userP, $threads, $nb, $pgas, $N, $optdist, $optrows, $optcols, $verbose, $quiet, $dryrun);

# Process args
GetOptions("n|nprocs=i" => \$ncpus,
           "nnodes:i"   => \$nnodes,
           "m|mem=s"    => \$mem,
           "N|ppn:i"    => \$ppn,
           "j:i"        => \$cpuspercu,
           "S:i"        => \$pps,
           "P:i"        => \$userP,
           "b|nb:i"     => \$nb,
           "d|depth:i"  => \$threads,
           "HPL_N:i"    => \$N,
           "optdist!"   => \$optdist,
           "optrows!"   => \$optrows,
           "optcols!"   => \$optcols,
           "verbose!"   => \$verbose,
           "quiet"      => \$quiet,
           "dryrun"     => \$dryrun) or &usage();

&usage() unless ((defined($ncpus) || defined($nnodes)) && (defined($mem) || defined($N)));

my $dirname = "$ncpus";
$dirname .= ".mem$mem"  if (defined($mem));
$dirname .= ".N$ppn"  if (defined($ppn));
$dirname .= ".d$threads" if (defined($threads));
$dirname .= ".j$cpuspercu" if (defined($cpuspercu));
$dirname .= ".S$pps" if (defined($pps));

$ppn = 16 unless (defined($ppn));
# $cpuspercu = 1 unless (defined($cpuspercu));
$threads = 1 unless (defined($threads));
$nb = $defaultNB unless (defined($nb));
$pgas = '' unless (defined($pgas));
$optdist = 0 unless (defined($optdist));
$optrows = 0 unless (defined($optrows));
$optcols = 0 unless (defined($optcols));
$verbose = 1 unless (defined($verbose));
$quiet = 0 unless (defined($quiet));
$verbose = 0 if ($quiet == 1);
$dryrun = 0 unless (defined($dryrun));
$mem = 0 unless (defined($mem));

# if (!defined($ncpus))
# {
#     $ncpus = $nnodes * $ppn;
# }
# else
# {
#     $nnodes = $ncpus/$ppn;
# }


if ($mem =~ /G/)
{
    $mem = $` * 1024;
}

$mem = $mem/2;

# Calculate process grid dimensions
my ($P, $Q);
if (defined($userP))
{
    $P = $userP;
    $Q = $ncpus/$P;
}
else
{
    $P = int(sqrt($ncpus));
    $Q = $ncpus/$P;
    while ( $Q !~ /^\d+$/ )
    {
        $P--;
        $Q = $ncpus/$P;
    }
}

# Calculate HPL matrix size
my $lcm;
if ($optdist)
{
    $lcm = &lcm( $P*$nb, $Q*$nb );
} elsif ($optrows)
{
    $lcm = $P*$nb;
} elsif ($optcols)
{
    $lcm = $Q*$nb;
}

if (!defined($N))
{
    if ($optdist || $optrows || $optcols)
    {
        $N = int(sqrt($mem * 131072 * $ncpus) / $lcm) * $lcm;
    } else {
        $N = int(sqrt($mem * 131072 * $ncpus) / $nb) * $nb;
    }
}

my $mbperproc = $N * $N / 131072 / $ncpus;

print "\nProblem size:      N = $N, using ";
printf '%5.1f', $mbperproc;
print " MB per process\n";

if ((($optdist || $optrows || $optcols) && $verbose) || $dryrun)
{
    print "Next largest optimal size: N = " . ($N + $lcm) . ", using ";
    $mbperproc = ($N + $lcm) * ($N + $lcm) / 131072 / $ncpus;
    printf '%5.1f', $mbperproc;
    print " MB per process\n";
}

# HPL runtime estimates

my $n_tflops = $N*$N*(2*$N/3 + 3/2);

my $target_percent_peak = 84 - int(0.025*sqrt($ncpus));

my $maxtime = 0.0;


if ($verbose)
{
    print "\n\tEstimated HPL runtime in hours:\n\n";
    print "\t               Percent of Peak\n";
    print "\tCPU GHz    " . ($target_percent_peak - 4) . "%    " .
          ($target_percent_peak -2 ). "%    " . ($target_percent_peak) .
          "%    " . ($target_percent_peak+2) . "%\n";
    print "\t-------   -----  -----  -----  -----\n";

    foreach my $cpu_ghz ( (2.5, 2.6, 2.7) )
    {
        print "\t  $cpu_ghz   ";

        foreach my $percent ( ($target_percent_peak - 4,
                               $target_percent_peak - 2,
                               $target_percent_peak,
                               $target_percent_peak + 2) )
        {
            print '  ';
            my $hours = $n_tflops / ($cpu_ghz * $threads * 4*2 * 1000000000 * $percent/100 * $ncpus) / 3600;
            $maxtime = $hours if ($maxtime < $hours);
            printf '%5.2f', $hours;
        }

        print "\n";
    }

    print "\n";
}

exit if ($dryrun);


my $walltime = int($maxtime + 5) . ':00:00';

# If a run directory already exists, we won't provide a runscript
if (! -e $dirname || (-e $dirname && ! -e "$dirname/runit"))
{
    if (! -e $dirname)
    {
        mkdir($dirname) or die "Unable to create directory `$dirname'!";
    }

    open(ESTIMATES, ">$dirname/estimates") or die
        "Unable to open file `$dirname/estimates'";
        
    print ESTIMATES"\nProblem size:      N = $N, using ";
    printf ESTIMATES"%5.1f", $mbperproc;
    print ESTIMATES" MB per process\n";
    print ESTIMATES"\n\tEstimated HPL runtime in hours:\n\n";
    print ESTIMATES"\t               Percent of Peak\n";
    print "\tCPU GHz    " . ($target_percent_peak - 4) . "%    " .
          ($target_percent_peak -2 ). "%    " . ($target_percent_peak) .
          "%    " . ($target_percent_peak+2) . "%\n";
    print ESTIMATES"\t-------   -----  -----  -----  -----\n";

    foreach my $cpu_ghz ( (2.5, 2.6, 2.7) )
    {
        print ESTIMATES"\t  $cpu_ghz   ";

        foreach my $percent ( ($target_percent_peak - 4,
                              $target_percent_peak - 2,
                              $target_percent_peak,
                              $target_percent_peak + 2) )
        {
            print ESTIMATES"  ";
            my $hours = $n_tflops / ($cpu_ghz * $threads * 4*2 * 1000000000 * $percent/100 * $ncpus) / 3600;
            $maxtime = $hours if ($maxtime < $hours);
            printf ESTIMATES"%5.2f", $hours;
        }

        print ESTIMATES"\n";
    }

    print ESTIMATES"\n";

        
        
    open(RUNIT, ">$dirname/runit") or die
        "Unable to open file `$dirname/runit'";

    my $mppnppn = $ppn * $threads;
    my $nodes = POSIX::ceil($ncpus / $ppn);
    my $mppwidth = $nodes * $mppnppn;
    $ppn = $ncpus if $ncpus < $ppn;

    print RUNIT "#!/bin/sh
#PBS -l mppwidth=$mppwidth
#PBS -l mppnppn=$mppnppn
#PBS -N hpl
#PBS -j oe
#PBS -l walltime=$walltime

. /opt/modules/default/init/sh
module load craype-hugepages32M

cat /etc/opt/cray/release/xtrelease
cat /etc/opt/cray/release/clerelease

cd \$PBS_O_WORKDIR

export MPICH_VERSION_DISPLAY=1
export MPICH_ENV_DISPLAY=1
export MPICH_CPUMASK_DISPLAY=1
" or die "Unable to write to file `$dirname/runit'!";

    my $aprun_options = '-ss -j 1' ;

    $aprun_options .= " -j $cpuspercu" if (defined($cpuspercu));
#     $aprun_options .= " -j $cpuspercu" ;

    if ($threads > 1)
    {
        print RUNIT "
export OMP_NUM_THREADS=$threads

aprun $aprun_options -n $ncpus -N $ppn -d $threads ";
    }
    else
    {
        print RUNIT "
aprun $aprun_options -n $ncpus -N $ppn ";
    }

    if (defined($pps))
    {
        print RUNIT "-S $pps ";
    }
    
    print RUNIT "../../bin/CrayXC/xhpl >& out.`date -Iseconds`
";

    close RUNIT or die "Unable to close file `$dirname/runit'!";
}
else
{
    # If a run directory exists, adjust the walltime

    open(RUNIT, "<$dirname/runit") or die
	"Unable to open file `$dirname/runit' for reading";

    my $runscript;
    {
	undef $/;
	$runscript = <RUNIT>;
    }

    close RUNIT or die
	"Unable to close file `$dirname/runit' after reading!";

    $runscript =~ s/(#PBS\s+-l\s+walltime=)([\d:]+)/$1$walltime/;

    if ($2 ne $walltime)
    {
        print "Changing walltime from $2 to $walltime.\n\n";

        open(RUNIT, ">$dirname/runit") or die
	    "Unable to open file `$dirname/runit' for writing";

        print RUNIT $runscript;

        close RUNIT or die
	    "Unable to close file `$dirname/runit' after writing!";
    }
}

open(HPLDAT, ">HPL.dat") or die
    "Unable to open file `HPL.dat'!";

print HPLDAT "HPLinpack benchmark input file
Innovative Computing Laboratory, University of Tennessee
HPL.out      output file name (if any)
6            device out (6=stdout,7=stderr,file)
1            # of problems sizes (N)
$N       Ns
1            # of NBs
$nb           NBs
0            PMAP process mapping (0=Row-,1=Column-major)
1            # of process grids (P x Q)
$P           Ps
$Q           Qs
16.0         threshold
1            # of panel fact
1            PFACTs (0=left, 1=Crout, 2=Right)
1            # of recursive stopping criterium
4            NBMINs (>= 1)
1            # of panels in recursion
2            NDIVs
1            # of recursive panel fact.
2            RFACTs (0=left, 1=Crout, 2=Right)
1            # of broadcast
1            BCASTs (0=1rg,1=1rM,2=2rg,3=2rM,4=Lng,5=LnM)
1            # of lookahead depth
0            DEPTHs (>=0)
2            SWAP (0=bin-exch,1=long,2=mix)
$nb           swapping threshold
0            L1 in (0=transposed,1=no-transposed) form
0            U  in (0=transposed,1=no-transposed) form
1            Equilibration (0=no,1=yes)
8            memory alignment in double (> 0)
" or die "Unable to write to file `HPL.dat'!";

close HPLDAT;

sub lcm($$)
{
    my ($g, $t, $a, $b) = (1, 0, @_);

    while ( (0 == ($a & 1)) && (0 == ($b & 1)) )
    {
	$a >>= 1;
	$b >>= 1;
	$g <<= 1;
    }

    while ($a > 0)
    {
	if (0 == ($a & 1)) { $a >>= 1; }
	elsif (0 == ($b & 1)) { $b >>= 1; }
	else
	{
	    $t = abs($a - $b) >> 1;
	    if ($a < $b) { $b = $t; }
	    else { $a = $t; }
	}
    }

    return $_[0]*$_[1]/($b*$g);
}
 
