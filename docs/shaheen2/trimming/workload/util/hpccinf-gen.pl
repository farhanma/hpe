#!/usr/bin/perl -w

use strict;
use Getopt::Long qw(:config no_ignore_case);
use Pod::Usage;
use POSIX;

my $A = 10;
my $B = 40;
my $nb = 168;

sub usage()
{
    print STDERR "Usage: $0 (-n nprocs|--nprocs=nprocs)\n" .
                 "          (-m mem|--mem=mem)\n" .	
                 "          [--nb=nb]\n" .
                 "          [--[no]optdist]\n" .
                 "          [-a A|--min=A] [-b B|--max=B]\n" .
                 "          [-v|--verbose]\n" .
                 "          [-q|--quiet]\n";
    print STDERR "  nprocs = number of MPI processes (aka core count)\n";
    print STDERR "  mem    = memory usage per process in MB\n" .
                 "           or GB with \"G\" suffix\n";
    print STDERR "  nb     = blocksize\n" .
                 "           default is $nb\n";
    print STDERR "  A      = minimum allowed number of PTRANS phases\n" .
                 "           default is $A\n";
    print STDERR "  B      = maximum allowed number of PTRANS phases\n" .
                 "           default is $B\n";
    print STDERR "  --[no]optdist : [don't try to] size problem to distribute evenly over procs\n";
    print STDERR "  -v|--verbose  : default amount of informative messages\n";
    print STDERR "  -q|--quiet    : no informative messages\n";
    print STDERR "  --dryrun      : don't write any files\n";
    exit;
}

&usage() unless (@ARGV > 2);

my ($ncpus, $mem, $userP, $N, $optdist, $optrows, $verbose, $quiet, $dryrun);

# Process args
GetOptions("n|nprocs=i" => \$ncpus,
           "m|mem=s"    => \$mem,
           "P:i"        => \$userP,
           "nb:i"       => \$nb,
           "HPL_N:i"    => \$N,
           "a|min:i"    => \$A,
           "b|max:i"    => \$B,
           "optdist!"   => \$optdist,
           "optrows!"   => \$optrows,
           "verbose!"   => \$verbose,
           "quiet"      => \$quiet,
           "dryrun"     => \$dryrun) or &usage();

&usage() unless (defined($ncpus) && (defined($mem) || defined($N)));

$optdist = 0 unless (defined($optdist));
$optrows = 0 unless (defined($optrows));
$verbose = 1 unless (defined($verbose));
$quiet = 0 unless (defined($quiet));
$verbose = 0 if ($quiet == 1);
$dryrun = 0 unless (defined($dryrun));
$mem = 0 unless (defined($mem));

if ($mem =~ /G/)
{
    $mem = $` * 1024;
}

# Choose process grid dimensions
my $count = 0;
my $n = $ncpus;
my ($l, $m);
my @P;
my @Q;
if (defined($userP))
{
    $P[$count] = $userP;
    $Q[$count] = $ncpus/$P[$count];
    $count++;
}
while ($count < 2 and $n > 0.9*$ncpus)
{
    $P[$count] = int(sqrt($n));
    $Q[$count] = $n/$P[$count];
    while ($count < 2 and $P[$count] > 0)
    {
	if ( $Q[$count] =~ /^\d+$/ )
	{
	    $l = &lcm($P[$count], $Q[$count]);
	    $m = $l/$P[$count];
	    if ($m >= $A and $m <= $B and
                !grep {$_ == $P[$count]} @P[0..$count-1] and
                $Q[$count]/$P[$count] < 2.01)
	    {
		my $phase = 'phase';
		$phase .= 's' if ($m > 1);
		print "$n = $P[$count] * $Q[$count]\t($m $phase)\n";
		$count++;
	    }
        }
	$P[$count]--;
	$Q[$count] = $n/$P[$count] unless (0 == $P[$count]);
    }
    $n--;
}

if ($count < 1)
{
    print STDERR "Unable to find PTRANS grid meeting ";
    print STDERR "$A <= number of phases <= $B.\n";
    exit 1;
}

# Calculate HPL matrix size
my $lcm;
if ($optdist)
{
    $lcm = &lcm( $P[0]*$nb, $Q[0]*$nb );
} elsif ($optrows)
{
    $lcm = $P[0]*$nb;
}

if (!defined($N))
{
    if ($optdist || $optrows)
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

if ((($optdist || $optrows) && $verbose) || $dryrun)
{
    print "Next largest optimal size: N = " . ($N + $lcm) . ", using ";
    $mbperproc = ($N + $lcm) * ($N + $lcm) / 131072 / $ncpus;
    printf '%5.1f', $mbperproc;
    print " MB per process\n";
}

open(HPLDAT, ">hpccinf.txt") or die
    "Unable to open file `hpccinf.txt'!";

$" = ' ';

print HPLDAT "HPLinpack benchmark input file
Innovative Computing Laboratory, University of Tennessee
HPL.out      output file name (if any)
6            device out (6=stdout,7=stderr,file)
1            # of problems sizes (N)
$N       Ns
1            # of NBs
$nb          NBs
0            PMAP process mapping (0=Row-,1=Column-major)
$count            # of process grids (P x Q)
@P[0..$count-1]           Ps
@Q[0..$count-1]           Qs
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
$nb          swapping threshold
0            L1 in (0=transposed,1=no-transposed) form
0            U  in (0=transposed,1=no-transposed) form
1            Equilibration (0=no,1=yes)
8            memory alignment in double (> 0)
##### This line (no. 32) is ignored (it serves as a separator). ######
0                               Number of additional problem sizes for PTRANS
1200                            values of N
5                             number of additional blocking sizes for PTRANS
7 13 23 31 63            values of NB
" or die "Unable to write to file `hpccinf.txt'!";

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
 
